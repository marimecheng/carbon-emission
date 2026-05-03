from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.responses import StreamingResponse
import io
from sqlalchemy.orm import Session
from sqlalchemy import func
from .database import engine, Base, get_db
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

from .ocr import extract_text_from_file
from .document_ai import extract_fields
from .calculator import compute_emissions
from .rag import store_document, get_history, get_hybrid_insights
from .predictor import forecast_next_month, predict_usage_impact
from .llm import generate_explanation
from .auth import router as auth_router
from .dependencies import get_current_user
from .dependencies import get_current_user
from .models import User, Emission
from .models import User, Emission
from .report_gen import generate_real_pdf

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AgentCarbon API")
app.include_router(auth_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class EmissionResponse(BaseModel):
    raw_text: str
    fields: dict
    emissions: dict
    history: list
    forecast: dict
    ml_predicted_co2: float | None = None
    explanation: str | None = None

@app.get("/history")
async def read_history(current_user: User = Depends(get_current_user)):
    try:
        data = get_history(user_id=current_user.id)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/insights")
async def read_insights(current_user: User = Depends(get_current_user)):
    try:
        data = get_hybrid_insights(user_id=current_user.id)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/history/{doc_id}")
async def delete_history_item(
    doc_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        from .rag import delete_document, get_document_by_id
        
        # 1. Fetch document details from Qdrant to identify Postgres row
        payload = get_document_by_id(doc_id)
        
        if payload:
            fields = payload.get("fields", {})
            emissions = payload.get("emissions", {})
            
            # Heuristic match for Postgres
            # Find and delete
            # We match on date, facility, and total_kgco2 as a "key"
            date = fields.get("date")
            facility = fields.get("facility_name", "Main Facility")
            co2 = float(emissions.get("total_kgco2") or 0.0)
            
            from .models import Emission
            # Delete one matching record (safest approach if duplicates exist, deletes just one instance corresponding to this doc)
            record = db.query(Emission).filter(
                Emission.date == date,
                Emission.facility_name == facility,
                Emission.total_kgco2 == co2
            ).first()
            
            if record:
                db.delete(record)
                db.commit()
                print(f"Deleted Postgres record: {record.id}")
            else:
                 print("No matching Postgres record found for deletion.")

        # 2. Delete from Qdrant/Neo4j
        success = delete_document(user_id=current_user.id, doc_id=doc_id)
        if not success:
             raise HTTPException(status_code=500, detail="Failed to delete document")
        return {"status": "deleted", "id": doc_id}
    except Exception as e:
        print(f"Delete Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/v1/models")
async def get_models():
    """Handle OpenAI-compatible /v1/models endpoint to reduce 404 noise."""
    return {"data": []}

@app.get("/report")
async def generate_user_report(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        from sqlalchemy import text, func

        # 2. Query REAL data from DB WITH FILTER
        res_co2 = db.query(func.sum(Emission.total_kgco2)).filter(Emission.user_id == current_user.id).scalar()
        res_kwh = db.query(func.sum(Emission.energy_kwh)).filter(Emission.user_id == current_user.id).scalar()
        
        # Force 0 if None
        total_co2 = float(res_co2) if res_co2 else 0.0
        total_kwh = float(res_kwh) if res_kwh else 0.0

        # 3. Print to terminal so you can see it working
        print(f"--- REPORT DEBUG ---")
        print(f"User: {current_user.email}")
        print(f"Database Result - CO2: {total_co2}, KWH: {total_kwh}")
        print(f"--------------------")

        # 4. Get Facility Data
        insights = get_hybrid_insights(user_id=current_user.id)
        facilities = insights.get("facilities", [])

        # 5. Generate PDF
        pdf_bytes = generate_real_pdf(
            email=current_user.email,
            total_co2=total_co2,
            total_kwh=total_kwh,
            facilities=facilities,
            ai_insights="Manual data verification complete. This report reflects live database values."
        )
        
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=ESG_Report.pdf"}
        )
    except Exception as e:
        print(f"CRITICAL REPORT ERROR: {e}")
        raise HTTPException(status_code=500, detail="Internal Report Error")

@app.post("/process", response_model=EmissionResponse)
async def process_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 1. Read file once
    content = await file.read()

    # 2. OCR
    try:
        raw_text = extract_text_from_file(content)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    # 3. Document understanding (regex-based for now)
    fields = extract_fields(raw_text)   # no image_bytes

    # 4. Emission calculation
    emissions = compute_emissions(fields)

    # 5. Store in RAG / history / Postgres
    _ = store_document(fields, emissions, current_user.id)
    
    # Store in Postgres (Schema isolated by get_current_user)
    from .models import Emission
    db_emission = Emission(
        user_id=current_user.id,
        facility_name=fields.get("facility_name", "Main Facility"),
        date=fields.get("date"),
        energy_kwh=float(fields.get("energy_kwh") or 0.0),
        water_gallons=float(fields.get("water_gallons") or 0.0),
        total_kgco2=float(emissions.get("total_kgco2") or 0.0)
    )
    db.add(db_emission)
    db.commit()

    # 6. Retrieve history + forecast
    history = get_history(current_user.id, limit=12)
    forecast = forecast_next_month(history)

    # 7. AI Prediction (Random Forest)
    # Ensure inputs are floats and protect against None
    kwh = float(fields.get("energy_kwh") or 0.0)
    gas = float(fields.get("gas_therms") or 0.0)
    water = float(fields.get("water_gallons") or 0.0)
    date_str = fields.get("date")
    
    ml_predicted_co2 = predict_usage_impact(kwh, gas, water, date_str)

    # 8. LLM explanation (Ollama Llama 3)
    explanation = generate_explanation(fields, emissions, history, ml_predicted_co2)

    return EmissionResponse(
        raw_text=raw_text,
        fields=fields,
        emissions=emissions,
        history=history,
        forecast=forecast,
        ml_predicted_co2=ml_predicted_co2,
        explanation=explanation,
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
