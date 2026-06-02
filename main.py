import asyncio
import logging
import sys
import datetime

from automation_server_client import (
    AutomationServer,
    Workqueue,
    WorkItemError,
    Credential,
    WorkItemStatus,
)
from momentum_client.manager import MomentumClientManager
from odk_tools.tracking import Tracker

tracker: Tracker
momentum: MomentumClientManager
proces_navn = (
    "Opfølgning på underskrift i forbindelse med tilbud om personlig assistance"
)


async def populate_queue(workqueue: Workqueue):
    logger = logging.getLogger(__name__)

    logger.info("Populating queue...")
    
    # Henter alle VITAS sager, der slutter efter dags dato.
    filters = [
        {
            "fieldName": "end",
            "values": [(datetime.date.today() + datetime.timedelta(days=1)).strftime("%Y-%m-%dT22:00:00.000Z"), None, "false"]
        }
    ]
    alle_vitas = momentum.vitas.hent_vitas(søgeterm="personlig assistance", filters=filters)

    for item in alle_vitas:
        vitas = momentum.vitas.hent_vita(item["id"])
        if vitas.get("statusCode") != "JOB_ALLOCATION_STATUS_GODKENDT_AF_BORGER": # svarer til "Borger har godkendt bevilling eller vurdering" i UI
            continue

        if not vitas.get("companySigner"):
            borger = momentum.borgere.hent_borger_med_id(vitas["citizenId"])

            # Check om borger allerede har opgaven
            opgaver = momentum.opgaver.hent_opgaver(borger)
            if any(
                opgave
                for opgave in opgaver
                if opgave.get("title")
                == "Opfølgning på underskrift i VITAS - Personlig Assistance"
                and opgave.get("stateName") == "Planlagt"
            ):
                continue

            workqueue.add_item(
                data={
                    "ansvarlig_sagsbehandler": vitas["responsibleCaseworker"],
                    "vitas_id": vitas["id"],
                    "borger_cpr": borger["cpr"],
                },
                reference=vitas["id"],
            )


async def process_workqueue(workqueue: Workqueue):
    logger = logging.getLogger(__name__)

    logger.info("Processing workqueue!")

    for item in workqueue:
        with item:
            data = item.data  # Item data deserialized from json as dict
            borger = momentum.borgere.hent_borger(data["borger_cpr"])

            try:
                opgave = momentum.opgaver.opret_opgave(
                    borger=borger,
                    medarbejdere=[data["ansvarlig_sagsbehandler"]["id"]],
                    forfaldsdato=datetime.datetime.today() + datetime.timedelta(days=14),
                    titel="Opfølgning på underskrift i VITAS - Personlig Assistance",
                    task_type=34,
                    beskrivelse="Sikrer underskrift fra Virksomheden på bevillingen af personlige assistance i VITAS",
                )
                if not opgave:
                    raise WorkItemError("Failed to create task in Momentum")

                tracker.track_task(process_name=proces_navn)

            except Exception as e:
                # A WorkItemError represents a soft error that indicates the item should be passed to manual processing or a business logic fault
                logger.error(f"Error processing item: {data}. Error: {e}")
                item.fail(str(e))


if __name__ == "__main__":
    ats = AutomationServer.from_environment()

    workqueue = ats.workqueue()

    # Initialize external systems for automation here..
    tracking_credential = Credential.get_credential("Odense SQL Server")
    tracker = Tracker(
        username=tracking_credential.username, password=tracking_credential.password
    )
    momentum_credential = Credential.get_credential("Momentum - produktion")
    momentum = MomentumClientManager(
        base_url=momentum_credential.data["base_url"],
        client_id=momentum_credential.username,
        client_secret=momentum_credential.password,
        api_key=momentum_credential.data["api_key"],
        resource=momentum_credential.data["resource"],
    )

    # Queue management
    if "--queue" in sys.argv:
        workqueue.clear_workqueue(WorkItemStatus.NEW)
        asyncio.run(populate_queue(workqueue))
        exit(0)

    # Process workqueue
    asyncio.run(process_workqueue(workqueue))
