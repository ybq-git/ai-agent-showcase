from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/generate_report', methods=['POST'])
def generate_report():
    data = request.get_json()
    keyword=data.get('keyword','默认工作')
    report=f"[{keyword}模拟周报]\n 完成开发，修复bug。"
    return jsonify({"report": report})

if __name__ == '__main__':
    app.run(debug=True,port=5000)