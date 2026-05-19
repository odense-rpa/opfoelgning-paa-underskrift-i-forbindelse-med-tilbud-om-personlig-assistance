import asyncio
import logging
import sys
import datetime

from automation_server_client import AutomationServer, Workqueue, WorkItemError, Credential, WorkItemStatus
from momentum_client.manager import MomentumClientManager
from odk_tools.tracking import Tracker


tracker: Tracker
momentum: MomentumClientManager
proces_navn = "Opfølgning på underskrift i forbindelse med tilbud om personlig assistance"


def fetch_borgere(borger_ids: list[str]) -> list[dict]:
    """Fetch citizens by their IDs."""
    borgere = []
    for borger_id in borger_ids:
        borger = momentum.borgere.hent_borger(borger_id)
        if borger:
            borgere.append(borger)
    return borgere


async def populate_queue(workqueue: Workqueue):
    logger = logging.getLogger(__name__)

    logger.info("Populating queue...")

    try:
        # Example: Define the citizen IDs to process
        # TODO: Replace with actual business logic to fetch citizens
        borger_ids = [
            # Add citizen IDs here
        ]

        borgere = fetch_borgere(borger_ids)

        for borger in borgere:
            workqueue.add_item(
                data={
                    'borger_id': borger['id'],
                    'cpr': borger.get('cpr'),
                },
                reference=borger.get('cpr') or borger.get('id')
            )

    except Exception as e:
        logger.error(f"Failed to populate queue: {e}")
        print(f"Error: {e}")
        return


async def process_workqueue(workqueue: Workqueue):
    logger = logging.getLogger(__name__)

    logger.info("Processing workqueue!")

    for item in workqueue:
        with item:
            data = item.data  # Item data deserialized from json as dict

            try:
                borger_id = data['borger_id']
                borger = momentum.borgere.hent_borger(borger_id)

                # TODO: Implement actual business logic for opfølgning på underskrift
                # Example operations:
                # - Check if citizen has signed required documents
                # - Create follow-up tasks or markers
                # - Track progress in Odense SQL Server

                # Uncomment when implementing:
                # momentum.borgere.opret_markering(
                #     borger=borger,
                #     start_dato=datetime.datetime.now().date(),
                #     markeringsnavn="Opfølgning på underskrift"
                # )
                # tracker.track_task(process_name=proces_navn)

            except WorkItemError as e:
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
