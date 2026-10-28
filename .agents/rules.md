## 1. プロジェクト概要

* **プロダクト名:** GrandReal（仮）
* **コンセプト:** 一人暮らしの高齢者と見守る家族を繋ぐ、監視感のない・低負荷な安否確認SNS
* **ターゲット:** 80代の一人暮らし高齢者 ＋ その家族（子ども世代）
* **主要コア機能:**
1. **1日1回のランダム通知 & 1タップ安否確認**（写真投稿または「今日は投稿しない」スキップ機能）
2. **ファミリーコントロール**（家族側からの遠隔設定・管理機能）
3. **認知機能維持クイズ**（顔写真と名前を思い出す回想脳トレ）
4. **見守りダッシュボード**（家族側の安否ステータス確認・タイムライン表示）



---

## 2. 開発環境・技術スタック

* **バックエンド:** Python / Django
* **フロントエンド:** HTML5 / Bootstrap 5 / JavaScript (Fetch API)
* **データベース:** PostgreSQL
* **DB設計・モデリングツール:** DBML (dbdiagram.io) / IE記法（クロウズフット記法）
* **UI/UX方針:** 高齢者配慮（大きなフォント・ボタン、シンプルな画面遷移、誤操作防止）

**注意：** migrateなどDjango関連のコマンドを打つにはWSLの指定したパス(/home/light/team-41/mimamori_sns)で `sudo docker-compose exec django python manage.py [command]` を実行する

---

## 3. データベース構造（DBML / IE記法）

データベースは **「1人につき1日1レコードの安否確認ログ (`safety_status_logs`)」** を軸に構成されています。

```dbml
Table users {
  user_id integer [primary key]
  name varchar [not null]
  role varchar [not null] // 'elderly' or 'family'
  email_address varchar [not null]
  profile_image_url varchar
  display_name varchar [not null]
  bio varchar
  created_at timestamp
}

Table family_relationships {
  relationship_id integer [primary key]
  elderly_user_id integer [not null]
  family_user_id integer [not null]
  created_at timestamp

  indexes {
    (elderly_user_id, family_user_id) [unique]
  }
}

Table safety_status_logs {
  log_id integer [primary key]
  elderly_user_id integer [not null]
  target_date date [not null] // いつの分のログか
  status_type varchar [not null] // 'photo', 'skip', 'unresponsive'
  responded_at timestamp // 実際に押された日時
  via_notification bool // 通知画面からの直押しフラグ

  indexes {
    (elderly_user_id, target_date) [unique] // 1人1日1件制約
  }
}

Table posts {
  post_id integer [primary key]
  log_id integer [not null]
  elderly_user_id integer [not null]
  image_url varchar
  caption text
  created_at timestamp
}

Table reaction {
  reaction_id integer [primary key]
  log_id integer [not null]
  family_user_id integer [not null]
  message varchar [not null]
  created_at timestamp
}

Table family_control_set {
  setting_id integer [primary key]
  elderly_user_id integer [not null, unique]
  notification_start_time time
  notification_end_time time
  alert_threshold_hours integer
}

Table notification {
  notification_id integer [primary key]
  receiver_user_id integer [not null]
  notification_type varchar
  sent_at timestamp
  is_read bool
}

Table follows {
  following_user_id integer [not null]
  followed_user_id integer [not null]
  created_at timestamp

  indexes {
    (following_user_id, followed_user_id) [pk]
  }
}

// リレーション
Ref: users.user_id < family_relationships.elderly_user_id
Ref: users.user_id < family_relationships.family_user_id
Ref: users.user_id < family_control_set.elderly_user_id
Ref: users.user_id < posts.elderly_user_id
Ref: users.user_id < safety_status_logs.elderly_user_id
Ref: users.user_id < reaction.family_user_id
Ref: users.user_id < notification.receiver_user_id
Ref: users.user_id < follows.following_user_id
Ref: users.user_id < follows.followed_user_id
Ref: safety_status_logs.log_id < reaction.log_id
Ref: safety_status_logs.log_id < posts.log_id

```

---

## 4. 現在の実装状況と次のタスク

### 既に実装済みの範囲（フロントエンド / Django）

* タイムライン画面のHTML/CSSテンプレート構成（Bootstrap 5採用）
* `Fetch API` を使用した非同期での画像ファイルアップロード処理
* 「本日の安否ステータス」「画像投稿」「今日は投稿しない（仮UI）」「過去の投稿フィード・コメント領域」のデザイン・レイアウト配置

---

## 5. 開発時の注意点・用語定義

* **UX・アクセシビリティ方針**
* 高齢者側画面はボタンを大きく（`btn-lg`）、文字サイズも十分な視認性を確保すること。
* ワンタップ（通知からのダイレクト操作など）で思考・操作の負担を最小限に抑える導線設計を徹底すること。