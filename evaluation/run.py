"""Run the 15-question benchmark and export human-review CSVs.

Usage: python evaluation/run.py [--base-url http://localhost:8000] [--no-upload]
       python evaluation/run.py --score evaluation/results
"""
import argparse
import csv
import json
from pathlib import Path
import urllib.error
import urllib.request
import uuid

ROOT = Path(__file__).resolve().parent.parent


def request_json(url, body=None, content_type=None):
    headers = {'Content-Type': content_type} if content_type else {}
    request = urllib.request.Request(url, data=body, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        raise RuntimeError(f'{url}: HTTP {error.code}: {error.read().decode(errors="replace")}') from error


def upload(base):
    boundary = '----policyqa' + uuid.uuid4().hex
    payload = bytearray()
    files = sorted((ROOT / 'sample_data').glob('*.pdf'))
    if len(files) != 3:
        raise RuntimeError('Expected three sample PDFs in sample_data/.')
    for path in files:
        payload.extend(f'--{boundary}\r\nContent-Disposition: form-data; name="files"; filename="{path.name}"\r\nContent-Type: application/pdf\r\n\r\n'.encode())
        payload.extend(path.read_bytes())
        payload.extend(b'\r\n')
    payload.extend(f'--{boundary}--\r\n'.encode())
    return request_json(base + '/api/documents', bytes(payload), 'multipart/form-data; boundary=' + boundary)


def write_csv(path, rows, fields):
    with path.open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def run(base, output, no_upload):
    questions = json.loads((ROOT / 'evaluation' / 'questions.json').read_text(encoding='utf-8-sig'))
    if not no_upload:
        upload(base)
    answers, citations, raw = [], [], []
    for index, item in enumerate(questions, 1):
        data = json.dumps({'question': item['question']}).encode()
        result = request_json(base + '/api/ask', data, 'application/json')
        raw.append({'benchmark': item, 'result': result})
        found = result.get('citations', [])
        answers.append({'id': item['id'], 'question': item['question'], 'reference_answer': item['reference_answer'],
                        'expected_document': item['document'], 'expected_page': item['page'], 'answer': result.get('answer', ''),
                        'citation_count': len(found), 'correct_1_or_0': '', 'review_notes': ''})
        for citation in found:
            citations.append({'question_id': item['id'], 'citation_id': citation.get('id'), 'answer': result.get('answer', ''),
                              'document': citation.get('document_name', ''), 'page': citation.get('page', ''),
                              'cited_text': citation.get('text', ''), 'grounded_1_or_0': '', 'review_notes': ''})
        print(f'[{index}/{len(questions)}] {item["id"]}: {len(found)} citation(s)')
    output.mkdir(parents=True, exist_ok=True)
    (output / 'responses.json').write_text(json.dumps(raw, indent=2, ensure_ascii=False), encoding='utf-8')
    write_csv(output / 'answers.csv', answers, ['id', 'question', 'reference_answer', 'expected_document', 'expected_page', 'answer', 'citation_count', 'correct_1_or_0', 'review_notes'])
    write_csv(output / 'citations.csv', citations, ['question_id', 'citation_id', 'answer', 'document', 'page', 'cited_text', 'grounded_1_or_0', 'review_notes'])
    print(f'\nReview {output / "answers.csv"} and {output / "citations.csv"}, then rerun with --score {output}.')


def score(output):
    def read(name):
        with (output / name).open(encoding='utf-8-sig', newline='') as handle:
            return list(csv.DictReader(handle))
    answers, citations = read('answers.csv'), read('citations.csv')
    for rows, field in [(answers, 'correct_1_or_0'), (citations, 'grounded_1_or_0')]:
        if any(row[field].strip() not in ('0', '1') for row in rows):
            raise ValueError(f'Every {field} cell must be reviewed and set to 0 or 1 before scoring.')
    if len(answers) != 15:
        raise ValueError('Expected exactly 15 answer rows.')
    correct = sum(int(row['correct_1_or_0']) for row in answers)
    grounded = sum(int(row['grounded_1_or_0']) for row in citations)
    covered = sum(int(row['citation_count']) > 0 for row in answers)
    print(f'Answer correctness: {correct}/15 = {correct / 15:.1%}')
    print(f'Citation grounding: {grounded}/{len(citations)} = {grounded / len(citations):.1%}' if citations else 'Citation grounding: undefined (no citations returned)')
    print(f'Citation coverage: {covered}/15 = {covered / 15:.1%}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url', default='http://localhost:8000')
    parser.add_argument('--no-upload', action='store_true', help='Use sample documents already present in the API corpus.')
    parser.add_argument('--output', type=Path, default=ROOT / 'evaluation' / 'results')
    parser.add_argument('--score', type=Path, help='Score completed review CSVs in this directory.')
    args = parser.parse_args()
    if args.score:
        score(args.score)
    else:
        run(args.base_url.rstrip('/'), args.output, args.no_upload)


if __name__ == '__main__':
    main()
