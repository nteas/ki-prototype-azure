export const enum RetrievalMode {
	Hybrid = 'hybrid',
	Vectors = 'vectors',
	Text = 'text',
}

export type AskRequestOverrides = {
	retrievalMode?: RetrievalMode;
	semanticRanker?: boolean;
	semanticCaptions?: boolean;
	excludeCategory?: string;
	top?: number;
	temperature?: number;
	promptTemplate?: string;
	promptTemplatePrefix?: string;
	promptTemplateSuffix?: string;
	suggestFollowupQuestions?: boolean;
	useOidSecurityFilter?: boolean;
	useGroupsSecurityFilter?: boolean;
};

export type AskRequest = {
	question: string;
	overrides?: AskRequestOverrides;
	idToken?: string;
};

export type ResponseMessage = {
	content: string;
	role: string;
};

export type ResponseExtraArgs = {
	thoughts: string | null;
	data_points: string[];
};

export type ResponseChoice = {
	index: number;
	message: ResponseMessage;
	extra_args: ResponseExtraArgs;
};

export type ChatAppResponseOrError = {
	choices?: ResponseChoice[];
	error?: string;
};

export type ChatAppResponse = {
	choices: ResponseChoice[];
};

export type ChatTurn = {
	user: string;
	bot?: string;
};

export type ChatRequest = {
	history: ChatTurn[];
	overrides?: AskRequestOverrides;
	idToken?: string;
	shouldStream?: boolean;
};

export enum DocumentTypeEnum {
	PDF = 'pdf',
	WEB = 'web',
}

export enum ClassificationEnum {
	public = 'public',
	internal = 'internal',
	confidential = 'confidential',
	powerSensitive = 'powerSensitive',
}

// classification map
export const classificationMap = {
	[ClassificationEnum.public]: 'Åpen',
	[ClassificationEnum.internal]: 'Intern',
	[ClassificationEnum.confidential]: 'Konfidensiell',
	[ClassificationEnum.powerSensitive]: 'Kraftsensitiv',
};

export type Log = {
	user?: string;
	change?: string;
	id?: string;
	message?: string;
	created_at: Date;
};

export type Document = {
	id: string;
	title?: string;
	owner?: string;
	classification?: ClassificationEnum;
	logs?: Log[];
	frequency?: string;
	type?: DocumentTypeEnum;
	file?: string;
	flagged_pages: string[];
	file_pages: string[];
	url?: string;
	created_at: Date;
	updated_at: Date;
	status?: string;
};
