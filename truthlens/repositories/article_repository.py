from truthlens.models import Article


def list_articles(category=None):
    query = Article.query
    if category:
        query = query.filter_by(category=category)
    return query.order_by(Article.published_at.desc()).all()
