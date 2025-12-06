"""Analysis endpoints"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from datetime import datetime
import logging

from app.schemas.analysis import TokenAddressRequest, AnalysisResponse
from app.schemas.status import StatusResponse
from app.schemas.graph import AnalysisDataModel
from app.services.analysis_service import AnalysisService
from app.services.export_service import ExportService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["analysis"])

# Global service instance (in production, use dependency injection)
analysis_service = AnalysisService(bitquery_api_key="ory_at_GvkHmlXX6ZDpF96XMfO9J4pEk-ZdqPAMzqcEKCATCAI.KIdkp5fUfNMeBjoxi49d4onFazuqXCFYgHAGadfHG8Q")
export_service = ExportService()


@router.post(
    "/analyze",
    response_model=AnalysisResponse,
    status_code=202,
    summary="Submit token for analysis",
    description="Submit a token contract address for blockchain forensics analysis. Returns immediately with analysis_id."
)
async def submit_analysis(
    request: TokenAddressRequest,
    background_tasks: BackgroundTasks
):
    """
    Submit a token for blockchain forensics analysis.

    Returns immediately (HTTP 202) with analysis_id. Processing happens in background.
    Use the analysis_id to poll for status and retrieve results.

    Example:
        ```json
        {
            "tokenAddress": "0x6982508145454ce325ddbe47a25d4ec3d2311933",
            "daysBack": 7,
            "sampleSize": 5000
        }
        ```
    """
    try:
        # Validate address format
        if not request.tokenAddress.startswith("0x") or len(request.tokenAddress) != 42:
            raise HTTPException(status_code=400, detail="Invalid token address format")

        # Submit analysis
        analysis_id = await analysis_service.submit_analysis(
            token_address=request.tokenAddress,
            days_back=request.daysBack,
            sample_size=request.sampleSize or 1000
        )

        # Queue background task
        background_tasks.add_task(
            analysis_service.run_analysis,
            analysis_id=analysis_id
        )

        logger.info(f"Analysis {analysis_id} submitted for token {request.tokenAddress}")

        return AnalysisResponse(
            analysisId=analysis_id,
            status="processing",
            timestamp=datetime.utcnow()
        )

    except Exception as e:
        logger.error(f"Failed to submit analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to submit analysis: {str(e)}")


@router.get(
    "/analysis/{analysis_id}/status",
    response_model=StatusResponse,
    summary="Get analysis status",
    description="Check the current status and progress of an analysis"
)
async def get_status(analysis_id: str):
    """
    Get real-time status of analysis.

    Returns current progress (0-100%), status, and current step.
    """
    try:
        status_data = await analysis_service.get_status(analysis_id)
        return StatusResponse(**status_data)
    except ValueError as e:
        logger.warning(f"Analysis not found: {analysis_id}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/analysis/{analysis_id}",
    response_model=AnalysisDataModel,
    summary="Get analysis results",
    description="Retrieve completed analysis results as AnalysisData"
)
async def get_results(analysis_id: str):
    """
    Get completed analysis results.

    Only available after analysis reaches 'completed' status.
    Returns full graph data, metrics, red flags, etc.
    """
    try:
        results = await analysis_service.get_results(analysis_id)
        return AnalysisDataModel(**results)
    except ValueError as e:
        logger.warning(f"Results not available: {analysis_id}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error retrieving results: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/analysis/{analysis_id}/export",
    summary="Export analysis results",
    description="Download analysis results in CSV or JSON format"
)
async def export_analysis(
    analysis_id: str,
    format: str = Query("json", description="Export format: 'csv' or 'json'")
):
    """
    Download analysis results in specified format.

    Supports CSV and JSON formats for integration with other tools.
    """
    try:
        # Get results
        results = await analysis_service.get_results(analysis_id)
        analysis_data = AnalysisDataModel(**results)

        # Export
        if format.lower() == "csv":
            content = export_service.export_to_csv(analysis_data)
            return {
                "format": "csv",
                "filename": f"analysis_{analysis_id}.csv",
                "content": content
            }
        elif format.lower() == "json":
            content = export_service.export_to_json(analysis_data)
            return {
                "format": "json",
                "filename": f"analysis_{analysis_id}.json",
                "content": content
            }
        else:
            raise HTTPException(status_code=400, detail="Format must be 'csv' or 'json'")

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error exporting: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/analyses",
    summary="List recent analyses",
    description="Get list of recent analyses with metadata"
)
async def list_analyses(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    List recent analyses.

    Returns paginated list of analyses with basic metadata.
    """
    try:
        results = await analysis_service.list_recent_analyses(limit, offset)
        return results
    except Exception as e:
        logger.error(f"Error listing analyses: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
