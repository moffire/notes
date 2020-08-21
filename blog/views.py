from django.shortcuts import render, get_object_or_404
from .models import Post
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django.views.generic import ListView
from .forms import EmailPostForm, CommentForm, SearchForm
from django.core.mail import send_mail
from notes.settings import user_host


class PostList(ListView):
    queryset = Post.published.all()
    context_object_name = 'posts'
    paginate_by = 2
    template_name = 'blog/post/list.html'


def post_detail(request, year, month, day, post):
    post = get_object_or_404(Post, slug=post, status='published', publish__year=year,
                             publish__month=month, publish__day=day)
    comments = post.comments.filter(active=True)
    new_comment = None
    if request.method == 'POST':
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            new_comment = comment_form.save(commit=False)
            new_comment.post = post
            new_comment.save()
    else:
        comment_form = CommentForm()
    return render(request, 'blog/post/detail.html', context={'post': post,
                                                             'comments': comments,
                                                             'new_comment': new_comment,
                                                             'comment_form': comment_form})


def post_share(request, post_id):
    post = get_object_or_404(Post, id=post_id, status='published')
    sent = False
    if request.method == 'POST':
        form = EmailPostForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            post_url = request.build_absolute_uri(post.get_absolute_url())
            subject = '{0} ({1}) recommends you reading "{2}"'.format(cd['name'], cd['email'], post.title)
            message = 'Read "{0}" at{1}\n\n{2}\'s comments: {1}'.format(post.title, post_url, cd['name'],
                                                                        cd['comments'])
            send_mail(subject, message, user_host, [cd['to']])
            sent = True
    else:
        form = EmailPostForm()
    return render(request, 'blog/post/share.html', context={'post': post, 'form': form, 'sent': sent})


def post_search(request):
    form = SearchForm()
    query = None
    if 'query' in request.GET:
        form = SearchForm(request.GET)
        if form.is_valid():
            query = form.cleaned_data['query']

            # specify the search priority
            search_vector = SearchVector('title', weight='A') + SearchVector('body', weight='B')

            search_query = SearchQuery(query)
            results = Post.objects.annotate(search=search_vector, rank=SearchRank(search_vector, search_query))\
                .filter(search=search_query).order_by('-rank')
            return render(request, 'blog/post/search.html', {'form': form,
                                                             'query': query,
                                                             'results': results})
    return render(request, 'blog/post/search.html', {'form': form})
