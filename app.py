#!/usr/bin/python3

import os
import time

import requests
from bs4 import BeautifulSoup
from flask import Flask, redirect, render_template, request
from opengraph import opengraph

TIKTOK_USERNAME = os.getenv("TIKTOK_USERNAME")


class Video:
    def __init__(self, data: BeautifulSoup):
        self.data = data
        self.banner = self.get_banner()
        self.url = self.get_url()
        self.description = self.get_description()

    def get_banner(self):
        return (
            self.data.find("div", {"class": "tiktok-1jxhpnd-DivContainer"})
            .find("img")
            .get("src")
        )

    def get_url(self):
        return (
            self.data.find("div", {"class": "tiktok-1s72ajp-DivWrapper"})
            .find("a")
            .get("href")
        )

    def get_description(self):
        return (
            self.data.find("div", {"class": "tiktok-1jxhpnd-DivContainer"})
            .find("img")
            .get("alt")
        )


class User:
    def __init__(self, username, image, bio):
        self.username = username
        self.image = image
        self.bio = bio.split(" | ")[1].split(" Followers")[0] + " Followers"


def get_user_info():
    url = f"https://www.tiktok.com/@{TIKTOK_USERNAME}"
    data = opengraph.OpenGraph(url=url)
    return User(TIKTOK_USERNAME, data["image"], data["description"])


def get_videos():
    base_url = f"https://www.tiktok.com/@{TIKTOK_USERNAME}"

    # get the html
    data = requests.get(base_url).text
    # parse the html
    soup = BeautifulSoup(data, "html.parser")

    # get all `user-post-item` divs
    posts = soup.find_all("div", {"data-e2e": "user-post-item"})

    videos = []
    # print
    for post in posts:
        videos.append(Video(post))

    return videos


app = Flask(__name__)


@app.route("/")
def loading():
    return render_template("loading.html")


@app.route("/index")
def index():
    return render_template("index.html", videos=get_videos(), user=get_user_info())


@app.route("/download")
def download_url():
    url = request.args.get("url")
    r = requests.post("https://snaptik.io/download/parse-url", data={"url": url}).json()
    print(url)
    while not r["code"] == 3:
        time.sleep(1)
        r = requests.post(
            "https://snaptik.io/download/parse-url", data={"url": url}
        ).json()

    return redirect(r["url"])

@app.route("/share")
def share():
    video_url = request.args.get("v")
    # nothing to share
    if not video_url:
        return redirect("/")
    # no tiktok url
    if not video_url.startswith("https://www.tiktok.com"):
        return redirect("/")
    # get video data
    data = requests.get(f"https://www.tiktok.com/oembed?url={video_url}").json()
    return render_template("share.html", video=data, user=get_user_info(), url=video_url)



if __name__ == "__main__":
    app.run(debug=False)
