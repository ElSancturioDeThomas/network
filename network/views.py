from django.contrib.auth import authenticate, login, logout
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_POST

from .models import User, Post, Comment


def index(request):
    posts = Post.objects.all().order_by("-timestamp")
    paginator = Paginator(posts, 10)  # Show 10 posts per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, "network/index.html", {
        "page_obj": page_obj,
        "posts": page_obj  # For backward compatibility with template
    })


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "network/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "network/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "network/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "network/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "network/register.html")

def create_post(request):
    if request.method == "POST":
        content = request.POST["content"]
        post = Post(user=request.user, content=content)
        post.save()
        return HttpResponseRedirect(reverse("index"))
    else:
        return HttpResponseRedirect(reverse("index"))

@require_POST
def edit_post(request, post_id):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Authentication required"}, status=403)
    
    post = get_object_or_404(Post, id=post_id)
    
    # Check if user owns the post
    if post.user != request.user:
        return JsonResponse({"error": "You can only edit your own posts"}, status=403)
    
    import json
    data = json.loads(request.body)
    content = data.get("content", "")
    
    if not content.strip():
        return JsonResponse({"error": "Content cannot be empty"}, status=400)
    
    post.content = content
    post.save()
    return JsonResponse({"message": "Post updated successfully", "content": post.content}, status=200)

@require_POST
def delete_post(request, post_id):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Authentication required"}, status=403)
    
    post = get_object_or_404(Post, id=post_id)
    
    # Check if user owns the post
    if post.user != request.user:
        return JsonResponse({"error": "You can only delete your own posts"}, status=403)
    
    # Get counts before deletion
    user = post.user
    total_posts = user.posts.count() - 1  # Subtract 1 since we're about to delete
    total_likes = user.get_total_likes() - post.likes.count()  # Subtract likes from this post
    
    post.delete()
    
    return JsonResponse({
        "message": "Post deleted successfully",
        "total_posts": total_posts,
        "total_likes": total_likes
    }, status=200)

def view_profile(request, username):
    profile_user = User.objects.get(username=username)
    # Filter posts to only show posts by this profile user
    posts = Post.objects.filter(user=profile_user).order_by("-timestamp")
    paginator = Paginator(posts, 10)  # Show 10 posts per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, "network/profile.html", {
        "profile_user": profile_user,
        "page_obj": page_obj,
        "posts": page_obj,  # For backward compatibility with template
        "total_posts": profile_user.total_posts(),
        "total_likes": profile_user.get_total_likes(),
    })
def view_following(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("login"))
    following = request.user.following.all()
    posts = Post.objects.filter(user__in=following).order_by("-timestamp")
    paginator = Paginator(posts, 10)  # Show 10 posts per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, "network/following.html", {
        "following": following,
        "page_obj": page_obj,
        "posts": page_obj,  # For backward compatibility with template
    })
@require_POST
def follow_user(request, user_id):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Authentication required"}, status=403)
    
    user_to_follow = get_object_or_404(User, id=user_id)
    
    # Check if user is trying to follow themselves
    if user_to_follow == request.user:
        return JsonResponse({"error": "You cannot follow yourself"}, status=400)
    
    # Toggle follow: if already following, unfollow; otherwise, follow
    if request.user.following.filter(id=user_id).exists():
        request.user.following.remove(user_to_follow)
        following = False
    else:
        request.user.following.add(user_to_follow)
        following = True
    
    return JsonResponse({
        "following": following,
        "followers_count": user_to_follow.get_followers_count()
    })

@require_POST
def like_post(request, post_id):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Authentication required"}, status=403)
    
    post = get_object_or_404(Post, id=post_id)
    
    # Toggle like: if user already liked, unlike; otherwise, like
    if post.likes.filter(id=request.user.id).exists():
        post.likes.remove(request.user)
        liked = False
    else:
        post.likes.add(request.user)
        liked = True
    
    # Get updated total likes for the post author (if on profile page)
    post_author_total_likes = post.user.get_total_likes()
    
    return JsonResponse({
        "liked": liked,
        "likes_count": post.likes.count(),
        "post_author_total_likes": post_author_total_likes,
        "post_author_id": post.user.id
    })

@require_POST
def comment_post(request, post_id):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Authentication required"}, status=403)
    
    post = get_object_or_404(Post, id=post_id)
    
    # Handle both form data and JSON
    if request.content_type == 'application/json':
        import json
        try:
            if request.body:
                data = json.loads(request.body)
                comment_content = data.get("content", "").strip()
            else:
                return JsonResponse({"error": "Empty request body"}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
    else:
        # Form data
        comment_content = request.POST.get("content", "").strip()
    
    if not comment_content:
        return JsonResponse({"error": "Comment cannot be empty"}, status=400)
    
    # Create a new comment
    comment = Comment(post=post, user=request.user, content=comment_content)
    comment.save()
    
    # If it's a form submission, redirect back to the page
    if request.content_type != 'application/json':
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse('index')))
    
    return JsonResponse({
        "message": "Comment added successfully",
        "comment_id": comment.id,
        "comment_content": comment.content,
        "comment_user": comment.user.username,
        "comment_timestamp": comment.timestamp.isoformat(),
        "comments_count": post.get_comments_count()
    }, status=200)