from flask import Flask, render_template, request, jsonify
import csv
import random
import os

app = Flask(__name__)

# CSV読み込み関数
def load_words(filename):
    words = []
    if not os.path.exists(filename): return []
    try:
        with open(filename, mode='r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            header = next(reader, None) # ヘッダーを飛ばす
            for row in reader:
                if len(row) >= 3:
                    words.append({
                        'Number': row[0].strip(),
                        'English': row[1].strip(),
                        'Japanese': row[2].strip()
                    })
    except Exception as e:
        print(f"Error loading {filename}: {e}")
    return words

# 苦手リスト(CSV)への保存関数
def save_weak_words(words):
    try:
        with open('weak_words.csv', mode='w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Number', 'English', 'Japanese'])
            for w in words:
                writer.writerow([w['Number'], w['English'], w['Japanese']])
    except Exception as e:
        print(f"Error saving weak words: {e}")

@app.route('/')
def index():
    return render_template('index.html')

# 問題データを送る処理
@app.route('/get_words', methods=['POST'])
def get_words():
    data = request.json
    mode = data.get('mode', 'normal')
    question_count = int(data.get('count', 10))
    ranges = data.get('ranges', [[1, 2027]]) 
    
    filename = 'weak_words.csv' if mode == 'weak' else 'words.csv'
    all_words = load_words(filename)
    
    if not all_words:
        return jsonify({"error": f"データが見つかりません。{filename}を確認してください。"})
        
    # ★修正：苦手モードの時は範囲の絞り込みをせず、リスト全体を対象にする
    if mode == 'weak':
        filtered_words = all_words
    else:
        filtered_words = []
        for w in all_words:
            try:
                num = int(w['Number'])
                in_range = False
                for r_start, r_end in ranges:
                    if r_start <= num <= r_end:
                        in_range = True
                        break
                if in_range:
                    filtered_words.append(w)
            except ValueError:
                continue
    
    if not filtered_words:
        return jsonify({"error": "選択された範囲に単語がありません。範囲指定を確認してください。"})
        
    sample_size = min(question_count, len(filtered_words))
    words = random.sample(filtered_words, sample_size)
    
    return jsonify({"words": words})

# 結果保存処理
@app.route('/save_results', methods=['POST'])
def save_results():
    data = request.json
    mode = data.get('mode')
    correct_words = data.get('correct_words', [])
    incorrect_words = data.get('incorrect_words', [])

    weak_words = load_words('weak_words.csv')
    weak_dict = {w['Number']: w for w in weak_words}

    # 間違えた単語を追加
    for w in incorrect_words:
        weak_dict[w['Number']] = w
        
    # 苦手モードで正解した単語は削除
    if mode == 'weak':
        for w in correct_words:
            if w['Number'] in weak_dict:
                del weak_dict[w['Number']]

    save_weak_words(list(weak_dict.values()))
    return jsonify({"status": "success"})

if __name__ == '__main__':
    app.run(debug=True)