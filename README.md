Prompt RAG design 

1. User Prompt
↓
2. Retrieval Check
	•	Search only in Ontario statutes, FAQs, and official forms.
	•	If top score < threshold → reply “Not found in uploaded sources.”
↓
3. Context-Limited Answering
	•	Every statement must be followed by a citation like [HCCA s.11].
	•	If no valid citation → replace with “Not supported by sources.”
↓
4. Output Rules
	•	No speculation.
	•	No external info unless in uploaded sources.
	•	No identifiers.
↓
5. Final Answer
✅ Grounded
✅ Concise
✅ Ontario-specific
✅ Citation-verified


