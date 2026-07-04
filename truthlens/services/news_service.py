import feedparser
import httpx
from datetime import datetime
from truthlens.extensions import db
from truthlens.models.article import Article
from truthlens.services.scoring import score_from_seed, score_label
from truthlens.utils.security import sanitize_html

CATEGORIES = ["Technology", "Politics", "Sports", "Finance", "Business", "Entertainment", "Health", "Science", "International"]

RSS_FEEDS = {
    "Technology": "http://feeds.bbci.co.uk/news/technology/rss.xml",
    "Science": "http://feeds.bbci.co.uk/news/science_and_environment/rss.xml",
    "Business": "http://feeds.bbci.co.uk/news/business/rss.xml",
    "International": "http://feeds.bbci.co.uk/news/world/rss.xml",
    "Entertainment": "http://feeds.bbci.co.uk/news/entertainment_and_arts/rss.xml",
    "Health": "http://feeds.bbci.co.uk/news/health/rss.xml"
}

FALLBACK_STORIES = [
    {
        "source": "BBC News",
        "title": "Quantum Computing breakthroughs reveal cryptographic risks",
        "summary": "Researchers demonstrate new algorithms capable of factoring large primes, threatening standard public key standards.",
        "category": "Technology",
        "score": 93,
    },
    {
        "source": "Reuters",
        "title": "Central banks coordinate interest rate strategies to combat rising inflation",
        "summary": "Top economic officials announce synchronized rate adjustments, targeting global market stabilization goals.",
        "category": "Finance",
        "score": 86,
    },
    {
        "source": "Associated Press",
        "title": "Election commissions address synthetic deepfake audio circulating in key states",
        "summary": "State security teams release identification heatmaps warning voters against unauthorized automated voice clips.",
        "category": "Politics",
        "score": 48,
    },
    {
        "source": "Scientific American",
        "title": "Fusion energy startup claims sustained net power gain in recent trial run",
        "summary": "Engineers report milestone after stabilizing magnetic fields for record durations, paving way for grid pilots.",
        "category": "Science",
        "score": 91,
    },
    {
        "source": "ESPN News",
        "title": "Global championship scheduling conflicts resolved after host city consensus",
        "summary": "Sports governing body releases revised tournaments calendar for the upcoming quadrennial games.",
        "category": "Sports",
        "score": 97,
    },
    {
        "source": "Health Daily",
        "title": "Linguistic patterns in public health announcements analyzed",
        "summary": "Researchers identify emotional framing increases message sharing but decreases comprehension index metrics.",
        "category": "Health",
        "score": 79,
    },
    {
        "source": "BBC News",
        "title": "Autonomous space exploration probes launch for asteroid belt surveying",
        "summary": "Deep space cameras and mineral spectrometers set to transmit asteroid core composition maps back to earth.",
        "category": "Science",
        "score": 95,
    },
    {
        "source": "Reuters",
        "title": "International trade consortium expands shipping security protocols",
        "summary": "New maritime monitoring arrays deployed across busy canals to track transport anomalies and route delays.",
        "category": "International",
        "score": 88,
    },
    {
        "source": "Variety Feed",
        "title": "Streaming platform announces digital watermark standards for original films",
        "summary": "Industry executives agree on standard pixel metadata tags to trace copyrights and prevent piracy scans.",
        "category": "Entertainment",
        "score": 76,
    },
    {
        "source": "Wall Street Journal",
        "title": "E-commerce platform logs surge in micro-merchant export volumes",
        "summary": "Cross-border retail logistics network reports record activity among independent cottage brands.",
        "category": "Business",
        "score": 89,
    }
]


def sync_news_articles():
    """
    Attempts to pull live stories from RSS feeds, classifies, computes trust scores, and persists to DB.
    """
    new_articles_count = 0
    
    # Try fetching RSS feeds
    for category, url in RSS_FEEDS.items():
        try:
            # Use httpx with 3s timeout to avoid blocking startup
            with httpx.Client(timeout=3.0) as client:
                res = client.get(url)
                if res.status_code == 200:
                    feed = feedparser.parse(res.text)
                    for entry in feed.entries[:6]:  # Pull top 6 from each feed
                        title = sanitize_html(entry.title)
                        
                        # Duplicate check
                        if Article.query.filter_by(title=title).first():
                            continue
                            
                        summary = sanitize_html(entry.get("summary", "No summary provided."))
                        if len(summary) > 280:
                            summary = summary[:277] + "..."
                            
                        source = "BBC News" if "bbc" in url else "Reuters"
                        score = score_from_seed(title)
                        
                        # Extract and parse date
                        published = datetime.utcnow()
                        if hasattr(entry, "published_parsed") and entry.published_parsed:
                            published = datetime(*entry.published_parsed[:6])

                        art = Article(
                            title=title,
                            summary=summary,
                            source=source,
                            category=category,
                            truthlens_score=score,
                            bias_label=["Left", "Center", "Right"][score % 3],
                            ai_risk=score_from_seed(title + "ai_risk", 5, 95),
                            published_at=published,
                            url=entry.get("link", "")
                        )
                        db.session.add(art)
                        new_articles_count += 1
        except Exception as e:
            # Silently log errors for local networking
            print(f"Error sync feed {category}: {e}")

    # Seed fallback dataset if DB has no articles
    if Article.query.count() == 0:
        for item in FALLBACK_STORIES:
            score = item["score"]
            art = Article(
                title=item["title"],
                summary=item["summary"],
                source=item["source"],
                category=item["category"],
                truthlens_score=score,
                bias_label=["Left", "Center", "Right"][score % 3],
                ai_risk=score_from_seed(item["title"] + "ai_risk", 5, 95),
                published_at=datetime.utcnow()
            )
            db.session.add(art)
            new_articles_count += 1
            
    db.session.commit()
    return new_articles_count


def get_top_stories():
    """
    Returns latest articles, ensuring database is seeded first.
    """
    if Article.query.count() == 0:
        sync_news_articles()
    
    db_items = Article.query.order_by(Article.published_at.desc()).limit(20).all()
    
    return [{
        "id": a.id,
        "title": a.title,
        "summary": a.summary,
        "source": a.source,
        "category": a.category,
        "topic": a.category,
        "score": a.truthlens_score,
        "label": score_label(a.truthlens_score),
        "bias": a.bias_label,
        "time": format_published_time(a.published_at)
    } for a in db_items]


def get_categories():
    """
    Queries DB or configurations.
    """
    if Article.query.count() == 0:
        sync_news_articles()
        
    results = []
    for name in CATEGORIES:
        articles_cat = Article.query.filter_by(category=name).all()
        count = len(articles_cat)
        avg = 75
        if count > 0:
            avg = int(sum(a.truthlens_score for a in articles_cat) / count)
        results.append({
            "name": name,
            "average_score": avg,
            "live_stories": count if count > 0 else 10
        })
    return results


def get_recommended_articles():
    return get_top_stories()[:4]


def search_articles(query: str):
    query = query.lower().strip()
    if not query:
        return get_top_stories()
    
    db_items = Article.query.filter(
        (Article.title.like(f"%{query}%")) | 
        (Article.summary.like(f"%{query}%")) | 
        (Article.category.like(f"%{query}%"))
    ).all()
    
    return [{
        "id": a.id,
        "title": a.title,
        "summary": a.summary,
        "source": a.source,
        "category": a.category,
        "topic": a.category,
        "score": a.truthlens_score,
        "label": score_label(a.truthlens_score),
        "time": format_published_time(a.published_at)
    } for a in db_items]


def format_published_time(dt: datetime) -> str:
    diff = datetime.utcnow() - dt
    if diff.total_seconds() < 60:
        return "Just now"
    minutes = int(diff.total_seconds() / 60)
    if minutes < 60:
        return f"{minutes} min ago"
    hours = int(minutes / 60)
    if hours < 24:
        return f"{hours} hours ago"
    return dt.strftime("%b %d")
