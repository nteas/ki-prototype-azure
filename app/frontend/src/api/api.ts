import { AskRequest, ChatAppResponse, ChatAppResponseOrError } from './models';
import { Log as TrackLog } from '../pages/logs/Logs';
const BACKEND_URI = '/api';

function getHeaders(): Record<string, string> {
	const headers: Record<string, string> = {
		'Content-Type': 'application/json',
	};

	return headers;
}

export async function askApi(options: AskRequest): Promise<ChatAppResponse> {
	const response = await fetch(`${BACKEND_URI}/ask`, {
		method: 'POST',
		headers: getHeaders(),
		body: JSON.stringify({
			question: options.question,
			overrides: {
				retrieval_mode: options.overrides?.retrievalMode,
				semantic_ranker: options.overrides?.semanticRanker,
				semantic_captions: options.overrides?.semanticCaptions,
				top: options.overrides?.top,
				temperature: options.overrides?.temperature,
				prompt_template: options.overrides?.promptTemplate,
				prompt_template_prefix: options.overrides?.promptTemplatePrefix,
				prompt_template_suffix: options.overrides?.promptTemplateSuffix,
				exclude_category: options.overrides?.excludeCategory,
				use_oid_security_filter:
					options.overrides?.useOidSecurityFilter,
				use_groups_security_filter:
					options.overrides?.useGroupsSecurityFilter,
			},
		}),
	});

	const parsedResponse: ChatAppResponseOrError = await response.json();
	if (response.status > 299 || !response.ok) {
		throw Error(parsedResponse.error || 'Unknown error');
	}

	return parsedResponse as ChatAppResponse;
}

export async function chatApi(question: string): Promise<Response> {
	return await fetch(`${BACKEND_URI}/chat_stream`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({
			question,
		}),
	});
}

export function getCitationFilePath(citation: string): string {
	return `${BACKEND_URI}/content/${citation}`;
}

interface AddLogProps {
	feedback: number;
	comment: string;
	thought_process: string;
}

export async function logChat(props: AddLogProps): Promise<Response> {
	return await fetch(`${BACKEND_URI}/logs/add`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
		},
		body: JSON.stringify({
			uuid:
				localStorage.getItem('ajs_anonymous_id')?.replace('"', '') ||
				'',
			feedback: props.feedback,
			comment: props.comment || '',
			timestamp: new Date().getTime(),
			thought_process: props.thought_process,
		}),
	});
}

export async function getChatLogs(): Promise<TrackLog[]> {
	return await fetch(`${BACKEND_URI}/logs`)
		.then(res => res.json())
		.then(data => data?.logs || []);
}
