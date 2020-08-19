from django.shortcuts import render, get_object_or_404
from .models import Post
from django.views.generic import ListView
from .forms import EmailPostForm
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
    return render(request, 'blog/post/detail.html', context={'post': post})


def post_share(request, post_id):
    post = get_object_or_404(Post, id=post_id, status='published')
    sent = False
    form = EmailPostForm()
    if request.method == 'POST':
        form = EmailPostForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            post_url = request.build_absolute_uri(post.get_absolute_url())
            subject = '{0} ({1}) recommends you reading "{2}"'.format(cd['name'], cd['email'], post.title)
            message = 'Read "{0}" at{1}\n\n{2}\'s comments: {1}'.format(post.title, post_url, cd['name'], cd['comments'])
            send_mail(subject, message, user_host, [cd['to']])
            sent = True
            return render(request, 'blog/post/share.html', context={'post': post, 'form': form, 'sent': sent})
        else:
            return render(request, 'blog/post/share.html', context={'post': post, 'form': form, 'sent': sent})
    else:
        return render(request, 'blog/post/share.html', context={'post': post, 'form': form, 'sent': sent})
