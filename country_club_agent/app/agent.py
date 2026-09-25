"""Country Club voice Agent definition.

Wires the Sofia persona (prompts.py) to the mock-data tools (tools/*.py)
using LiveKit Agents' function-tool pattern, and configures Gemini Live as
the realtime speech-to-speech model.
"""

from __future__ import annotations

import logging
from typing import Optional

from livekit.agents import Agent, RunContext, function_tool

from .prompts import SYSTEM_INSTRUCTIONS
from .tools import activities as activities_tool
from .tools import events as events_tool
from .tools import golf as golf_tool
from .tools import reservations as reservations_tool
from .tools import restaurants as restaurants_tool

logger = logging.getLogger("country-club-agent")


class CountryClubAgent(Agent):
    """Sofia - the Santo Domingo Country Club voice assistant.

    All business data comes from static JSON mock files (see /mock_data); there
    is no database, ORM, or external API call involved in this POC.
    """

    def __init__(self) -> None:
        super().__init__(instructions=SYSTEM_INSTRUCTIONS)

    # ------------------------------------------------------------------
    # Tool: club & activity information
    # ------------------------------------------------------------------
    @function_tool()
    async def get_activity_info(
        self,
        context: RunContext,
        activity: Optional[str] = None,
    ) -> dict:
        """Get information about club activities/sports.

        Call this when the customer asks what activities/sports the club
        offers, or asks about a specific one (tennis, padel, swimming,
        fitness, racquetball). For golf specifically, prefer
        get_golf_info for deeper detail.

        Args:
            activity: The activity the customer asked about, if any
                (e.g. "tennis", "pádel"). Leave empty to list all
                activities.
        """
        logger.info("tool_call get_activity_info activity=%s", activity)
        return activities_tool.get_activity_info(activity)

    @function_tool()
    async def get_club_overview(self, context: RunContext) -> dict:
        """Get general club information: name, history, areas, hours, and
        contact details. Call this for general "tell me about the club" /
        hours / contact / address questions.
        """
        logger.info("tool_call get_club_overview")
        return activities_tool.get_club_overview()

    # ------------------------------------------------------------------
    # Tool: golf information
    # ------------------------------------------------------------------
    @function_tool()
    async def get_golf_info(
        self,
        context: RunContext,
        topic: Optional[str] = None,
    ) -> dict:
        """Get golf information: course details, carts, caddies, golf shop,
        on-course dining, or reservations.

        Args:
            topic: Optional narrower topic (e.g. "course", "carts",
                "caddies", "shop", "dining", "reservations"). Leave empty
                for a general overview.
        """
        logger.info("tool_call get_golf_info topic=%s", topic)
        return golf_tool.get_golf_info(topic)

    # ------------------------------------------------------------------
    # Tool: restaurant information
    # ------------------------------------------------------------------
    @function_tool()
    async def get_restaurant_info(
        self,
        context: RunContext,
        restaurant: Optional[str] = None,
    ) -> dict:
        """Get information about the club's dining venues.

        Args:
            restaurant: The venue the customer asked about, if any
                (e.g. "Hoyo 19", "SportsBar"). Leave empty to list all
                dining venues.
        """
        logger.info("tool_call get_restaurant_info restaurant=%s", restaurant)
        return restaurants_tool.get_restaurant_info(restaurant)

    # ------------------------------------------------------------------
    # Tool: event / venue information
    # ------------------------------------------------------------------
    @function_tool()
    async def get_event_info(
        self,
        context: RunContext,
        venue: Optional[str] = None,
    ) -> dict:
        """Get information about event spaces/salons (capacity, event
        types, facilities).

        Args:
            venue: The venue the customer asked about, if any (e.g.
                "Salón Cristal"). Leave empty to list all event venues.
        """
        logger.info("tool_call get_event_info venue=%s", venue)
        return events_tool.get_event_info(venue)

    # ------------------------------------------------------------------
    # Tool: check mock availability
    # ------------------------------------------------------------------
    @function_tool()
    async def check_mock_availability(
        self,
        context: RunContext,
        service: str,
        date: str,
        time: str,
        guests: int,
        location: Optional[str] = None,
    ) -> dict:
        """Check if a service is available on a specific date and time for
        a given number of guests. Use this BEFORE creating any reservation.

        If the requested slot is not available, the tool returns alternative
        time slots that have capacity. Present these alternatives to the
        customer and let them choose.

        Args:
            service: The service type the customer wants. Use one of:
                "golf", "restaurant", "tennis", "padel", "event".
            date: The requested date in ISO format, e.g. "2026-09-26".
            time: The requested time in 24-hour format, e.g. "09:00".
            guests: Number of people or guests.
            location: For restaurant or event reservations, the specific
                venue name (e.g. "Hoyo 19", "Salón Cristal"). Not needed
                for golf, tennis, or padel.
        """
        logger.info(
            "tool_call check_mock_availability service=%s date=%s time=%s guests=%d location=%s",
            service, date, time, guests, location,
        )
        return reservations_tool.check_mock_availability(
            service=service,
            date=date,
            time=time,
            guests=guests,
            location=location,
        )

    # ------------------------------------------------------------------
    # Tool: create mock reservation
    # ------------------------------------------------------------------
    @function_tool()
    async def create_mock_reservation(
        self,
        context: RunContext,
        service: str,
        date: str,
        time: str,
        guests: int,
        customer_name: str,
        location: Optional[str] = None,
    ) -> dict:
        """Create a mock reservation ONLY after:
        1. Availability has been confirmed via check_mock_availability.
        2. The customer's name has been collected.
        3. All details have been summarized and the customer has
           explicitly confirmed with "yes" or equivalent.

        NEVER call this tool without explicit customer confirmation.

        Args:
            service: The service type, e.g. "golf", "restaurant", "event".
            date: Reservation date in ISO format, e.g. "2026-09-26".
            time: Reservation time in 24-hour format, e.g. "09:00".
            guests: Number of people or guests.
            customer_name: The name the reservation should be under.
            location: For restaurant or event reservations, the venue name.
        """
        logger.info(
            "tool_call create_mock_reservation service=%s date=%s time=%s guests=%d name=%s location=%s",
            service, date, time, guests, customer_name, location,
        )
        return reservations_tool.create_mock_reservation(
            service=service,
            date=date,
            time=time,
            guests=guests,
            customer_name=customer_name,
            location=location,
        )

    # ------------------------------------------------------------------
    # Tool: send mock OTP
    # ------------------------------------------------------------------
    @function_tool()
    async def send_mock_otp(
        self,
        context: RunContext,
        reservation_id: str,
        phone: str,
        email: str,
    ) -> dict:
        """Send a 4-digit verification code (OTP) to the customer's phone
        and email to confirm their reservation.

        Call this AFTER create_mock_reservation and AFTER collecting the
        customer's phone number and email address.

        Args:
            reservation_id: The reservation ID returned by
                create_mock_reservation (e.g. "CC-10001").
            phone: The customer's phone number.
            email: The customer's email address.
        """
        logger.info(
            "tool_call send_mock_otp reservation_id=%s phone=%s email=%s",
            reservation_id, phone, email,
        )
        return reservations_tool.send_mock_otp(
            reservation_id=reservation_id,
            phone=phone,
            email=email,
        )

    # ------------------------------------------------------------------
    # Tool: verify mock OTP
    # ------------------------------------------------------------------
    @function_tool()
    async def verify_mock_otp(
        self,
        context: RunContext,
        reservation_id: str,
        otp_code: str,
    ) -> dict:
        """Verify the OTP code the customer provides and confirm their
        reservation.

        Call this AFTER send_mock_otp, once the customer tells you the
        4-digit code they received.

        Args:
            reservation_id: The reservation ID (e.g. "CC-10001").
            otp_code: The 4-digit code provided by the customer.
        """
        logger.info(
            "tool_call verify_mock_otp reservation_id=%s otp_code=%s",
            reservation_id, otp_code,
        )
        return reservations_tool.verify_mock_otp(
            reservation_id=reservation_id,
            otp_code=otp_code,
        )

