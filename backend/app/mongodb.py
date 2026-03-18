from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.config import settings

_client: AsyncIOMotorClient | None = None


async def connect_mongodb() -> None:
    global _client
    _client = AsyncIOMotorClient(settings.MONGODB_URI)

    # Import all document models here so Beanie can initialise them
    from app.mongo_models.opportunity_mongo import OpportunityDocument
    from app.mongo_models.tariff_mongo import TariffPriceDocument
    from app.mongo_models.patient_mongo import PatientDocument, PrescriptionDocument
    from app.mongo_models.analytics_mongo import PatientAnalyticsDocument
    from app.mongo_models.medication_mongo import MedicationDocument
    from app.mongo_models.drug_class_mongo import DrugClassDocument
    from app.mongo_models.sync_log_mongo import SyncLogDocument, MedSyncLogDocument, TariffSyncLogDocument
    from app.mongo_models.measure_mongo import PracticeMeasureDocument
    from app.mongo_models.report_mongo import ICBReportDocument

    await init_beanie(
        database=_client[settings.MONGODB_DB_NAME],
        document_models=[
            OpportunityDocument,
            TariffPriceDocument,
            PatientDocument,
            PrescriptionDocument,
            PatientAnalyticsDocument,
            MedicationDocument,
            DrugClassDocument,
            SyncLogDocument,
            MedSyncLogDocument,
            TariffSyncLogDocument,
            PracticeMeasureDocument,
            ICBReportDocument,
        ],
    )
    print(f"[MongoDB] Connected to {settings.MONGODB_DB_NAME}")


async def disconnect_mongodb() -> None:
    global _client
    if _client:
        _client.close()
        print("[MongoDB] Disconnected")
