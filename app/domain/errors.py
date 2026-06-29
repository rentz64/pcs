class DomainError(Exception):
    """Base error for application/domain failures."""


class InvalidCredentials(DomainError):
    pass


class InvalidToken(DomainError):
    pass


class UnknownUser(DomainError):
    pass


class ContentNotFound(DomainError):
    pass


class StoredObjectNotFound(DomainError):
    pass


class BlogPostNotFound(DomainError):
    pass


class DuplicateSlug(DomainError):
    pass


class InvalidBlogPost(DomainError):
    pass


class ExternalSourceNotFound(DomainError):
    pass


class ExternalAccountNotFound(DomainError):
    pass


class ImportJobNotFound(DomainError):
    pass


class ImportAdapterNotFound(DomainError):
    pass


class JobNotFound(DomainError):
    pass


class InvalidJobState(DomainError):
    pass


class JobAttemptsExhausted(DomainError):
    pass


class TaskHandlerNotFound(DomainError):
    pass


class InvalidMediaType(DomainError):
    pass


class MediaItemNotFound(DomainError):
    pass


class EmailMessageNotFound(DomainError):
    pass


class EmailAttachmentNotFound(DomainError):
    pass


class InvalidEmailPayload(DomainError):
    pass


class TravelItineraryNotFound(DomainError):
    pass


class TravelPlaceNotFound(DomainError):
    pass


class TravelRouteNotFound(DomainError):
    pass


class InvalidTravelItinerary(DomainError):
    pass


class InvalidTravelPlace(DomainError):
    pass


class InvalidTravelRoute(DomainError):
    pass

