from fastapi import APIRouter, Depends, HTTPException

from app.application.blog_use_cases import BlogPostUseCases
from app.application.dto import CreateBlogPostCommand, UpdateBlogPostCommand
from app.domain.blog import BlogPost
from app.domain.entities import User
from app.domain.errors import BlogPostNotFound, DuplicateSlug, InvalidBlogPost
from app.interfaces.api.dependencies import current_user, get_blog_post_use_cases
from app.interfaces.api.schemas import BlogPostCreate, BlogPostOut, BlogPostUpdate

router = APIRouter(prefix="/blog/posts")


def _out(post: BlogPost) -> BlogPostOut:
    return BlogPostOut(
        id=post.id,
        content_item_id=post.content_item.id,
        title=post.title,
        slug=post.slug,
        body=post.body,
        summary=post.summary,
        status=post.status.value,
        created_at=post.created_at,
        updated_at=post.updated_at,
        published_at=post.published_at,
        tags=post.tags,
        collections=(),
    )


@router.post("", response_model=BlogPostOut)
def create_post(
    payload: BlogPostCreate,
    blogs: BlogPostUseCases = Depends(get_blog_post_use_cases),
    user: User = Depends(current_user),
) -> BlogPostOut:
    try:
        return _out(
            blogs.create_draft(
                user,
                CreateBlogPostCommand(
                    title=payload.title,
                    slug=payload.slug,
                    body=payload.body,
                    summary=payload.summary,
                    tags=payload.tags,
                    collections=payload.collections,
                ),
            )
        )
    except DuplicateSlug:
        raise HTTPException(status_code=409, detail="Slug already exists")
    except InvalidBlogPost as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("", response_model=list[BlogPostOut])
def list_posts(
    q: str = "",
    blogs: BlogPostUseCases = Depends(get_blog_post_use_cases),
    user: User = Depends(current_user),
) -> list[BlogPostOut]:
    posts = blogs.search_posts(user, q) if q else blogs.list_posts(user)
    return [_out(post) for post in posts]


@router.get("/slug/{slug}", response_model=BlogPostOut)
def get_post_by_slug(
    slug: str,
    blogs: BlogPostUseCases = Depends(get_blog_post_use_cases),
    user: User = Depends(current_user),
) -> BlogPostOut:
    try:
        return _out(blogs.get_by_slug(user, slug))
    except BlogPostNotFound:
        raise HTTPException(status_code=404, detail="Blog post not found")


@router.get("/{post_id}", response_model=BlogPostOut)
def get_post(
    post_id: int,
    blogs: BlogPostUseCases = Depends(get_blog_post_use_cases),
    user: User = Depends(current_user),
) -> BlogPostOut:
    try:
        return _out(blogs.get_by_id(user, post_id))
    except BlogPostNotFound:
        raise HTTPException(status_code=404, detail="Blog post not found")


@router.put("/{post_id}", response_model=BlogPostOut)
def update_post(
    post_id: int,
    payload: BlogPostUpdate,
    blogs: BlogPostUseCases = Depends(get_blog_post_use_cases),
    user: User = Depends(current_user),
) -> BlogPostOut:
    try:
        return _out(
            blogs.update_draft(
                user,
                post_id,
                UpdateBlogPostCommand(
                    title=payload.title,
                    slug=payload.slug,
                    body=payload.body,
                    summary=payload.summary,
                    tags=payload.tags,
                    collections=payload.collections,
                ),
            )
        )
    except BlogPostNotFound:
        raise HTTPException(status_code=404, detail="Blog post not found")
    except DuplicateSlug:
        raise HTTPException(status_code=409, detail="Slug already exists")
    except InvalidBlogPost as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/{post_id}/publish", response_model=BlogPostOut)
def publish_post(
    post_id: int,
    blogs: BlogPostUseCases = Depends(get_blog_post_use_cases),
    user: User = Depends(current_user),
) -> BlogPostOut:
    try:
        return _out(blogs.publish(user, post_id))
    except BlogPostNotFound:
        raise HTTPException(status_code=404, detail="Blog post not found")
    except InvalidBlogPost as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/{post_id}/unpublish", response_model=BlogPostOut)
def unpublish_post(
    post_id: int,
    blogs: BlogPostUseCases = Depends(get_blog_post_use_cases),
    user: User = Depends(current_user),
) -> BlogPostOut:
    try:
        return _out(blogs.unpublish(user, post_id))
    except BlogPostNotFound:
        raise HTTPException(status_code=404, detail="Blog post not found")
