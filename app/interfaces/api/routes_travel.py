from fastapi import APIRouter, Depends, HTTPException

from app.application.dto import (
    AddTravelPlaceCommand,
    AddTravelRouteCommand,
    CreateTravelItineraryCommand,
    UpdateTravelItineraryCommand,
    UpdateTravelPlaceCommand,
    UpdateTravelRouteCommand,
)
from app.application.travel_use_cases import TravelUseCases
from app.domain.entities import User
from app.domain.errors import (
    InvalidTravelItinerary,
    InvalidTravelPlace,
    InvalidTravelRoute,
    TravelItineraryNotFound,
    TravelPlaceNotFound,
    TravelRouteNotFound,
)
from app.domain.travel import TravelItinerary, TravelPlace, TravelRoute
from app.interfaces.api.dependencies import current_user, get_travel_use_cases
from app.interfaces.api.schemas import (
    TravelItineraryCreate,
    TravelItineraryOut,
    TravelItineraryUpdate,
    TravelPlaceCreate,
    TravelPlaceOut,
    TravelPlaceUpdate,
    TravelRouteCreate,
    TravelRouteOut,
    TravelRouteUpdate,
)

router = APIRouter(prefix="/travel")


def _place_out(place: TravelPlace) -> TravelPlaceOut:
    return TravelPlaceOut(
        id=place.id,
        itinerary_id=place.itinerary_id,
        name=place.name,
        description=place.description,
        address=place.address,
        latitude=place.latitude,
        longitude=place.longitude,
        visit_start=place.visit_start,
        visit_end=place.visit_end,
        sequence_order=place.sequence_order,
    )


def _route_out(route: TravelRoute) -> TravelRouteOut:
    return TravelRouteOut(
        id=route.id,
        itinerary_id=route.itinerary_id,
        origin_place_id=route.origin_place_id,
        destination_place_id=route.destination_place_id,
        transport_mode=route.transport_mode,
        distance_meters=route.distance_meters,
        duration_seconds=route.duration_seconds,
        sequence_order=route.sequence_order,
    )


def _itinerary_out(itinerary: TravelItinerary) -> TravelItineraryOut:
    return TravelItineraryOut(
        id=itinerary.id,
        content_item_id=itinerary.content_item.id,
        title=itinerary.title,
        description=itinerary.description,
        start_date=itinerary.start_date,
        end_date=itinerary.end_date,
        status=itinerary.status.value,
        places=[_place_out(place) for place in itinerary.places],
        routes=[_route_out(route) for route in itinerary.routes],
        created_at=itinerary.created_at,
        updated_at=itinerary.updated_at,
    )


@router.post("/itineraries", response_model=TravelItineraryOut)
def create_itinerary(
    payload: TravelItineraryCreate,
    travel: TravelUseCases = Depends(get_travel_use_cases),
    user: User = Depends(current_user),
) -> TravelItineraryOut:
    try:
        return _itinerary_out(
            travel.create_itinerary(
                user,
                CreateTravelItineraryCommand(
                    title=payload.title,
                    description=payload.description,
                    start_date=payload.start_date,
                    end_date=payload.end_date,
                    status=payload.status,
                ),
            )
        )
    except InvalidTravelItinerary as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/itineraries", response_model=list[TravelItineraryOut])
def list_itineraries(
    q: str = "",
    travel: TravelUseCases = Depends(get_travel_use_cases),
    user: User = Depends(current_user),
) -> list[TravelItineraryOut]:
    rows = travel.search_itineraries(user, q) if q else travel.list_itineraries(user)
    return [_itinerary_out(row) for row in rows]


@router.get("/itineraries/{itinerary_id}", response_model=TravelItineraryOut)
def get_itinerary(
    itinerary_id: int,
    travel: TravelUseCases = Depends(get_travel_use_cases),
    user: User = Depends(current_user),
) -> TravelItineraryOut:
    try:
        return _itinerary_out(travel.get_itinerary(user, itinerary_id))
    except TravelItineraryNotFound:
        raise HTTPException(status_code=404, detail="Travel itinerary not found")


@router.put("/itineraries/{itinerary_id}", response_model=TravelItineraryOut)
def update_itinerary(
    itinerary_id: int,
    payload: TravelItineraryUpdate,
    travel: TravelUseCases = Depends(get_travel_use_cases),
    user: User = Depends(current_user),
) -> TravelItineraryOut:
    try:
        return _itinerary_out(
            travel.update_itinerary(
                user,
                itinerary_id,
                UpdateTravelItineraryCommand(
                    title=payload.title,
                    description=payload.description,
                    start_date=payload.start_date,
                    end_date=payload.end_date,
                    status=payload.status,
                ),
            )
        )
    except TravelItineraryNotFound:
        raise HTTPException(status_code=404, detail="Travel itinerary not found")
    except InvalidTravelItinerary as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/itineraries/{itinerary_id}/places", response_model=TravelPlaceOut)
def add_place(
    itinerary_id: int,
    payload: TravelPlaceCreate,
    travel: TravelUseCases = Depends(get_travel_use_cases),
    user: User = Depends(current_user),
) -> TravelPlaceOut:
    try:
        return _place_out(
            travel.add_place(
                user,
                itinerary_id,
                AddTravelPlaceCommand(
                    name=payload.name,
                    description=payload.description,
                    address=payload.address,
                    latitude=payload.latitude,
                    longitude=payload.longitude,
                    visit_start=payload.visit_start,
                    visit_end=payload.visit_end,
                    sequence_order=payload.sequence_order,
                ),
            )
        )
    except TravelItineraryNotFound:
        raise HTTPException(status_code=404, detail="Travel itinerary not found")
    except InvalidTravelPlace as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.put("/places/{place_id}", response_model=TravelPlaceOut)
def update_place(
    place_id: int,
    payload: TravelPlaceUpdate,
    travel: TravelUseCases = Depends(get_travel_use_cases),
    user: User = Depends(current_user),
) -> TravelPlaceOut:
    try:
        return _place_out(
            travel.update_place(
                user,
                place_id,
                UpdateTravelPlaceCommand(
                    name=payload.name,
                    description=payload.description,
                    address=payload.address,
                    latitude=payload.latitude,
                    longitude=payload.longitude,
                    visit_start=payload.visit_start,
                    visit_end=payload.visit_end,
                    sequence_order=payload.sequence_order,
                ),
            )
        )
    except TravelPlaceNotFound:
        raise HTTPException(status_code=404, detail="Travel place not found")
    except InvalidTravelPlace as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/places/{place_id}")
def remove_place(
    place_id: int,
    travel: TravelUseCases = Depends(get_travel_use_cases),
    user: User = Depends(current_user),
) -> dict[str, str]:
    try:
        travel.remove_place(user, place_id)
        return {"status": "deleted"}
    except TravelPlaceNotFound:
        raise HTTPException(status_code=404, detail="Travel place not found")


@router.post("/itineraries/{itinerary_id}/routes", response_model=TravelRouteOut)
def add_route(
    itinerary_id: int,
    payload: TravelRouteCreate,
    travel: TravelUseCases = Depends(get_travel_use_cases),
    user: User = Depends(current_user),
) -> TravelRouteOut:
    try:
        return _route_out(
            travel.add_route(
                user,
                itinerary_id,
                AddTravelRouteCommand(
                    origin_place_id=payload.origin_place_id,
                    destination_place_id=payload.destination_place_id,
                    transport_mode=payload.transport_mode,
                    distance_meters=payload.distance_meters,
                    duration_seconds=payload.duration_seconds,
                    sequence_order=payload.sequence_order,
                ),
            )
        )
    except TravelItineraryNotFound:
        raise HTTPException(status_code=404, detail="Travel itinerary not found")
    except InvalidTravelRoute as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.put("/routes/{route_id}", response_model=TravelRouteOut)
def update_route(
    route_id: int,
    payload: TravelRouteUpdate,
    travel: TravelUseCases = Depends(get_travel_use_cases),
    user: User = Depends(current_user),
) -> TravelRouteOut:
    try:
        return _route_out(
            travel.update_route(
                user,
                route_id,
                UpdateTravelRouteCommand(
                    origin_place_id=payload.origin_place_id,
                    destination_place_id=payload.destination_place_id,
                    transport_mode=payload.transport_mode,
                    distance_meters=payload.distance_meters,
                    duration_seconds=payload.duration_seconds,
                    sequence_order=payload.sequence_order,
                ),
            )
        )
    except TravelRouteNotFound:
        raise HTTPException(status_code=404, detail="Travel route not found")
    except InvalidTravelRoute as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/routes/{route_id}")
def remove_route(
    route_id: int,
    travel: TravelUseCases = Depends(get_travel_use_cases),
    user: User = Depends(current_user),
) -> dict[str, str]:
    try:
        travel.remove_route(user, route_id)
        return {"status": "deleted"}
    except TravelRouteNotFound:
        raise HTTPException(status_code=404, detail="Travel route not found")
