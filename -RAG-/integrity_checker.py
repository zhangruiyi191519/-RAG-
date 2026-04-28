"""
    数据校验器
"""
import os
import json
import hashlib
import config_data as config
import schedule
import time

os.makedirs(config.snapshot_path, exist_ok=True)

# 获取每个片段的md5值
def get_md5(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()

# 导入数据时，创建快照，并且为每一个snapshot生成一个签名，防止篡改
def create_snapshot(document_id: str, chunks: list):
    snapshot = {
        "document_id": document_id,
        "chunk_total": len(chunks),
        "chunks": []
    }

    for idx, chunk in enumerate(chunks):
        snapshot["chunks"].append({
            "chunk_id": idx,
            "md5": get_md5(chunk)
        })

    # 生成签名
    snapshot_str = json.dumps(snapshot, sort_keys=True)
    signature = hashlib.sha256(snapshot_str.encode("utf-8")).hexdigest()

    snapshot_with_sig = {
        "data": snapshot,
        "signature": signature
    }

    file_path = os.path.join(config.snapshot_path, f"{document_id}.json")

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(snapshot_with_sig, f, ensure_ascii=False, indent=2)

    return file_path

# 读取快照
def load_snapshot(document_id: str):
    path = os.path.join(config.snapshot_path, f"{document_id}.json")

    if not os.path.exists(path):
        return None

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# 校验函数
def check_document(chroma, document_id: str):
    
    snapshot_with_sig = load_snapshot(document_id)

    if snapshot_with_sig is None:
        return f"[错误] 找不到 snapshot: {document_id}"

    # 签名校验
    if not verify_signature(snapshot_with_sig):
        return f"[严重错误] snapshot被篡改: {document_id}"

    snapshot = snapshot_with_sig["data"]

    if snapshot is None:
        return f"[错误] 找不到 snapshot: {document_id}"

    # 从数据库取数据
    results = chroma.get(where={"document_id": document_id})

    docs = results["documents"]
    metadatas = results["metadatas"]

    errors = []

    # 数量校验
    if len(docs) != snapshot["chunk_total"]:
        errors.append(
            f"chunk数量不一致：当前{len(docs)}，应为{snapshot['chunk_total']}"
        )

    # 构建当前chunk映射
    current_chunks = {}
    for doc, meta in zip(docs, metadatas):
        cid = meta.get("chunk_id")
        current_chunks[cid] = doc

    # 逐个校验
    for item in snapshot["chunks"]:
        cid = item["chunk_id"]
        expected_md5 = item["md5"]

        if cid not in current_chunks:
            errors.append(f"缺失 chunk_id={cid}")
            continue

        actual_md5 = get_md5(current_chunks[cid])

        if actual_md5 != expected_md5:
            errors.append(f"chunk_id={cid} 内容被篡改")

    # 返回结果
    if not errors:
        return f"[正常] document_id={document_id}"

    return f"[异常] document_id={document_id} -> " + " | ".join(errors)

# 签名校验函数
def verify_signature(snapshot_with_sig: dict) -> bool:
    data = snapshot_with_sig["data"]
    signature = snapshot_with_sig["signature"]

    snapshot_str = json.dumps(data, sort_keys=True)
    new_signature = hashlib.sha256(snapshot_str.encode("utf-8")).hexdigest()

    return new_signature == signature

# 扫描所有文件
def scan_all_documents(chroma):
    results = []

    for file in os.listdir(config.snapshot_path):
        if not file.endswith(".json"):
            continue

        document_id = file.replace(".json", "")
        result = check_document(chroma, document_id)

        results.append(result)

    return results

# 报警函数
def alert(results: list):
    abnormal = [r for r in results if "[异常]" in r or "[严重错误]" in r]

    if abnormal:
        print("⚠数据完整性异常：")
        for r in abnormal:
            print(r)
    else:
        print("所有文档正常")

# 校验任务
def run_daily_check(chroma):
    print("开始完整性校验...")

    results = scan_all_documents(chroma)

    for r in results:
        print(r)

    alert(results)

# 任务调度器
def start_scheduler(chroma):
    # 每天凌晨2点执行
    schedule.every().day.at("00:00").do(run_daily_check, chroma=chroma)

    print("定时任务已启动...")

    while True:
        schedule.run_pending()
        time.sleep(60)