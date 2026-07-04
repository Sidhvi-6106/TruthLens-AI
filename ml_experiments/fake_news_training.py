import re

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split


def clean_text(text: str) -> str:
    text = str(text)
    text = re.sub(r"\W", " ", text)
    return " ".join(text.lower().split())


def train_fake_news_baseline(true_csv: str, fake_csv: str):
    real_news = pd.read_csv(true_csv, sep=",", on_bad_lines="skip", quoting=3)
    fake_news = pd.read_csv(fake_csv, sep=",", on_bad_lines="skip", quoting=3)
    real_news["label"] = 1
    fake_news["label"] = 0

    data = pd.concat([real_news, fake_news]).sample(frac=1, random_state=42).reset_index(drop=True)
    data["text"] = data["text"].fillna("").map(clean_text)

    x_train, x_test, y_train, y_test = train_test_split(
        data["text"],
        data["label"],
        test_size=0.2,
        random_state=42,
    )

    vectorizer = TfidfVectorizer(max_features=5000)
    x_train_tfidf = vectorizer.fit_transform(x_train)
    x_test_tfidf = vectorizer.transform(x_test)

    model = LogisticRegression(max_iter=1000)
    model.fit(x_train_tfidf, y_train)

    predictions = model.predict(x_test_tfidf)
    print("Accuracy:", accuracy_score(y_test, predictions))
    print(classification_report(y_test, predictions))
    return model, vectorizer


if __name__ == "__main__":
    train_fake_news_baseline("data/True.csv", "data/Fake.csv")
