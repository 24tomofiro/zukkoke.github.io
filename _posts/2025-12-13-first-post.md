---
layout: post
read_time: true
show_date: true
title: "GitHub Pagesを使って完全無料でブログを開設する方法"
date: 2025-12-13
img: posts/20251213/github-pages-setup.jpg
tags: [github, blog, jekyll, markdown, tutorial]
category: tech
author: Admin
description: "サーバー代もドメイン代も不要。GitHub Pagesを使って、Markdownで管理できる自分だけのブログサイトを構築する手順をまとめました。"
---
最近、個人のナレッジベースや日記としてブログを始めたいと考える人が増えています。しかし、WordPressなどはサーバー代がかかったり、無料ブログサービスだと広告が入ったりカスタマイズに制限があったりと、一長一短です。

そこで今回は、エンジニアや技術好きの間で定番となっている**GitHub Pages**を使ったブログ作成方法を紹介します。

![GitHub Pages setup](./assets/img/posts/20251213/github-repo.jpg)
<small>[GitHub Pages](https://pages.github.com/) はGitHubのリポジトリから直接ウェブサイトをホスティングできる静的サイトホスティングサービスです。</small>

### なぜGitHub Pagesなのか？

最大のメリットは**「完全無料」**であること、そして**「Markdownで記事が書ける」**ことです。
特に普段からNotionやObsidianなどでメモを取っている人にとって、そのテキストをそのままブログとして公開できるのは大きな魅力です。

<tweet>GitHub Pagesを使えば、サーバー費用ゼロで、Markdownファイルを置くだけの高速なブログサイトが構築できます。</tweet>

### 作成のステップ

構築は驚くほどシンプルです。主な手順は以下の通りです。

#### 1. GitHubリポジトリの作成
まず、GitHubのアカウントを作成し、新しいリポジトリを作成します。
リポジトリ名は必ず `ユーザー名.github.io` にする必要があります。これがそのままあなたのブログのURLになります。

#### 2. 静的サイトジェネレーター（Jekyll）の活用
HTMLを直接書いても良いですが、ブログとして運用するなら**Jekyll**などの静的サイトジェネレーターを使うのが効率的です。
設定ファイル（`_config.yml`）を一つ置き、Jekyllのテーマを適用するだけで、プロ並みのデザインが手に入ります。

#### 3. 記事の作成と公開
あとは `_posts` というフォルダの中に、Markdownファイル（`.md`）を追加していくだけです。
Gitコマンドを使って変更をPush（アップロード）すれば、数分後には世界中に公開されます。

### 実際にやってみた感想

最初は「黒い画面（ターミナル）」を使うことに抵抗があるかもしれませんが、慣れてしまえばブラウザ上のエディタよりも遥かに高速に執筆できます。
また、GitHub上で履歴管理ができるため、「いつ何を修正したか」が明確に残るのも大きなメリットです。

<iframe width="560" height="315" src="https://www.youtube.com/embed/2MsN8gpT6jY" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>

### 今後の展望

このブログ自体もGitHub Pagesで運用しています。
今後は独自ドメインの適用や、Google Analyticsによるアクセス解析の導入など、さらにカスタマイズを進めていく予定です。

もし「自分だけの城（ウェブサイト）」を持ちたいと考えているなら、ぜひこの週末に試してみてください。

<tweet>自分のコンテンツの著作権とデータを完全にコントロールできるのが、自作ブログの最大の強みです。</tweet>

![Writing Markdown](./assets/img/posts/20251213/markdown-editor.jpg)
<small>VS Codeなどのエディタを使えば、プレビューを見ながら快適に執筆作業が進められます。</small>