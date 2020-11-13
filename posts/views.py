from django.shortcuts import render, get_object_or_404
from django.shortcuts import redirect
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator


from .models import Post, Group, User, Comment, Follow
from .forms import PostForm, CommentForm


def index(request):
    post_list = Post.objects.order_by("-pub_date").all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(
         request,
         "index.html",
         {"page": page, "paginator": paginator}
     )


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
         request,
         "group.html",
         {"group": group, 'page': page, 'paginator': paginator}
     )


@login_required
def new_post(request):
    form = PostForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            form.save()
            return redirect("index")
    return render(request, "new_post.html", {
                                            "form": form,
                                            "flag": True
                                            })


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    is_follow = author.following.filter(user=request.user.id).exists()
    return render(
        request,
        "profile.html",
        {
            "author": author,
            "user": request.user,
            "page": page,
            "paginator": paginator,
            "following": is_follow
        }
    )


def post_view(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, id=post_id)
    comments = post.comments.all()
    form = CommentForm(request.POST or None)

    return render(
        request,
        "post.html",
        {"author": post.author, "post": post, "comments": comments, "form": form}
    )


def post_edit(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, id=post_id)
    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=post)
    if request.method == "POST":
        if form.is_valid():
            post.text = form.cleaned_data["text"]
            post.group = form.cleaned_data["group"]
            post.save()
            return redirect(
                "post",
                username=username,
                post_id=post_id
            )
    return render(
        request,
        "new_post.html",
        {
            "form": form,
            "post": post,
            "flag": False
        }
    )


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, id=post_id)
    form = CommentForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            return redirect(
                "post",
                username=username,
                post_id=post_id
            )
    return render(
        request,
        "post.html",
        {
            "form": form,
            "post": post
        }
    )


def page_not_found(request, exception):
    return render(
        request, 
        "misc/404.html", 
        {"path": request.path}, 
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)


@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(
        request,
        "follow.html",
        {
            "page": page,
            "paginator": paginator
        }
    )

@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect("profile", username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()
    return redirect("profile", username=username)
