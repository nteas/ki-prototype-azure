import { Marked } from '@ts-stack/markdown';

type Citation = {
	title: string;
	url: string;
};

type HtmlParsedAnswer = {
	answerHtml: string;
	citations: Citation[];
	followupQuestions: string[];
};

export function parseAnswerToHtml(
	answer: string,
	isStreaming: boolean
): HtmlParsedAnswer {
	const citations: Citation[] = [];
	const followupQuestions: string[] = [];

	// Extract any follow-up questions that might be in the answer
	let parsedAnswer = answer.replace(/<<([^>>]+)>>/g, (match, content) => {
		followupQuestions.push(content);
		return '';
	});

	// trim any whitespace from the end of the answer after removing follow-up questions
	parsedAnswer = parsedAnswer.trim();

	// Omit a citation that is still being typed during streaming
	if (isStreaming) {
		let lastIndex = parsedAnswer.length;
		for (let i = parsedAnswer.length - 1; i >= 0; i--) {
			if (parsedAnswer[i] === ']') {
				break;
			} else if (parsedAnswer[i] === '[') {
				lastIndex = i;
				break;
			}
		}
		const truncatedAnswer = parsedAnswer.substring(0, lastIndex);
		parsedAnswer = truncatedAnswer;
	}

	const parts = parsedAnswer.split('separator');

	// a list of citations in the format [title](url). the title might contain parentheses, so we need to handle that
	const citationRegex = /\[([^\]]+)\]\(([^)]+)\)/g;
	let citationMatch;
	while ((citationMatch = citationRegex.exec(parts[1]))) {
		const title = citationMatch[1];
		const url = citationMatch[2];
		citations.push({ title, url });
	}

	return {
		answerHtml: Marked.parse(parts[0]),
		citations,
		followupQuestions,
	};
}
