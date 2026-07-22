"""Task-generation + skill-matching pipeline for domain pools.

Standalone project (parked in the skillproof repo). Public surface:
  corpus.load_corpus / score_corpus / select_seeds  — difficulty-targeted seeds
  difficulty.score_text / score_chunk / rank        — the difficulty prior
  authoring.authoring_prompt / harden_prompt        — Harbor task authoring contract
  match.relevances / build_plan / classify_to_domain — skill matching (skill-blind)
See pipeline/README.md for the full stage design and the Harbor probe/harden seam.
"""
