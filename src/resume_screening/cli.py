"""Command-line interface."""
import argparse
import json
from src.resume_screening.pipeline import screen_resumes,save_results

def main():
    parser=argparse.ArgumentParser(description="Rank PDF resumes against a PDF/TXT job description.")
    parser.add_argument("--jd",required=True)
    parser.add_argument("--resumes",nargs="+",required=True)
    parser.add_argument("--output",default="data/outputs/results.json")
    args=parser.parse_args()
    results=screen_resumes(args.resumes,args.jd)
    save_results(results,args.output)
    print(json.dumps([{"rank":x["rank"],"filename":x["filename"],"final_score":x["final_score"],"category_scores":x["category_scores"]} for x in results],indent=2))
    rejected=results[0].get("rejected_candidates",[]) if results else []
    if rejected:
        print("\nRejected resumes:")
        for item in rejected: print(f"- {item['filename']}: {item['reason']}")

if __name__=="__main__": main()
