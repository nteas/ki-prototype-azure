import { useRef, useState, useEffect } from 'react';
import {
	Checkbox,
	Panel,
	DefaultButton,
	TextField,
	SpinButton,
	Dropdown,
	IDropdownOption,
} from '@fluentui/react';
import readNDJSONStream from 'ndjson-readablestream';

import styles from './Chat.module.css';

import {
	chatApi,
	RetrievalMode,
	ChatAppResponse,
	ChatAppResponseOrError,
	ChatRequest,
	ChatTurn,
} from '../../api';
import { Answer, AnswerError, AnswerLoading } from '../../components/Answer';
import { QuestionInput } from '../../components/QuestionInput';
import { ExampleList } from '../../components/Example';
import { UserChatMessage } from '../../components/UserChatMessage';
import {
	AnalysisPanel,
	AnalysisPanelTabs,
} from '../../components/AnalysisPanel';
import { SettingsButton } from '../../components/SettingsButton';
import { ClearChatButton } from '../../components/ClearChatButton';
import { useLogin, getToken } from '../../authConfig';
import { useMsal } from '@azure/msal-react';
import { TokenClaimsDisplay } from '../../components/TokenClaimsDisplay';
import Layout from '../../components/Layout/Layout';
import { FinishChatButton } from '../../components/FinishChat/FinishChatButton';
import analytics from '../../libs/analytics';

const Chat = () => {
	const [isConfigPanelOpen, setIsConfigPanelOpen] = useState(false);
	const [promptTemplate, setPromptTemplate] = useState<string>('');
	const [retrieveCount, setRetrieveCount] = useState<number>(3);
	const [retrievalMode, setRetrievalMode] = useState<RetrievalMode>(
		RetrievalMode.Hybrid
	);
	const [useSemanticRanker, setUseSemanticRanker] = useState<boolean>(true);
	const [shouldStream, setShouldStream] = useState<boolean>(true);
	const [useSemanticCaptions, setUseSemanticCaptions] =
		useState<boolean>(false);
	const [excludeCategory, setExcludeCategory] = useState<string>('');
	const [useSuggestFollowupQuestions, setUseSuggestFollowupQuestions] =
		useState<boolean>(false);
	const [useOidSecurityFilter, setUseOidSecurityFilter] =
		useState<boolean>(false);
	const [useGroupsSecurityFilter, setUseGroupsSecurityFilter] =
		useState<boolean>(false);

	const lastQuestionRef = useRef<string>('');
	const chatMessageStreamEnd = useRef<HTMLDivElement | null>(null);

	const [isLoading, setIsLoading] = useState<boolean>(false);
	const [isStreaming, setIsStreaming] = useState<boolean>(false);
	const [error, setError] = useState<unknown>();

	const [activeCitation, setActiveCitation] = useState<string>();
	const [activeAnalysisPanelTab, setActiveAnalysisPanelTab] = useState<
		AnalysisPanelTabs | undefined
	>(undefined);

	const [selectedAnswer, setSelectedAnswer] = useState<number>(0);
	const [answers, setAnswers] = useState<
		[user: string, response: ChatAppResponse][]
	>([]);
	const [streamedAnswers, setStreamedAnswers] = useState<
		[user: string, response: ChatAppResponse][]
	>([]);

	const timer = useRef<number>(0);

	const handleAsyncRequest = async (
		question: string,
		answers: [string, ChatAppResponse][],
		setAnswers: Function,
		responseBody: ReadableStream<any>
	) => {
		let answer: string = '';
		let askResponse: ChatAppResponse = {} as ChatAppResponse;

		const updateState = (newContent: string) => {
			return new Promise(resolve => {
				setTimeout(() => {
					answer += newContent;
					const latestResponse: ChatAppResponse = {
						...askResponse,
						choices: [
							{
								...askResponse.choices[0],
								message: {
									content: answer,
									role: askResponse.choices[0].message.role,
								},
							},
						],
					};
					setStreamedAnswers([
						...answers,
						[question, latestResponse],
					]);
					resolve(null);
				}, 33);
			});
		};
		try {
			setIsStreaming(true);
			for await (const event of readNDJSONStream(responseBody)) {
				if (
					event['choices'] &&
					event['choices'][0]['extra_args'] &&
					event['choices'][0]['extra_args']['data_points']
				) {
					event['choices'][0]['message'] =
						event['choices'][0]['delta'];
					askResponse = event;
				} else if (
					event['choices'] &&
					event['choices'][0]['delta']['content']
				) {
					setIsLoading(false);
					await updateState(event['choices'][0]['delta']['content']);
				}
			}
		} finally {
			setIsStreaming(false);
		}
		const fullResponse: ChatAppResponse = {
			...askResponse,
			choices: [
				{
					...askResponse.choices[0],
					message: {
						content: answer,
						role: askResponse.choices[0].message.role,
					},
				},
			],
		};
		return fullResponse;
	};

	const client = useLogin ? useMsal().instance : undefined;

	const makeApiRequest = async (question: string) => {
		await analytics.track('Question Asked', {
			question,
			timestamp: Math.round(new Date().getTime() / 1000),
		});

		lastQuestionRef.current = question;

		if (timer.current === 0) {
			timer.current = new Date().getTime();
		}

		error && setError(undefined);
		setIsLoading(true);
		setActiveCitation(undefined);
		setActiveAnalysisPanelTab(undefined);

		const token = client ? await getToken(client) : undefined;

		try {
			const history: ChatTurn[] = answers.map(a => ({
				user: a[0],
				bot: a[1].choices[0].message.content,
			}));
			const request: ChatRequest = {
				history: [...history, { user: question, bot: undefined }],
				shouldStream: shouldStream,
				overrides: {
					promptTemplate:
						promptTemplate.length === 0
							? undefined
							: promptTemplate,
					excludeCategory:
						excludeCategory.length === 0
							? undefined
							: excludeCategory,
					top: retrieveCount,
					retrievalMode: retrievalMode,
					semanticRanker: useSemanticRanker,
					semanticCaptions: useSemanticCaptions,
					suggestFollowupQuestions: useSuggestFollowupQuestions,
					useOidSecurityFilter: useOidSecurityFilter,
					useGroupsSecurityFilter: useGroupsSecurityFilter,
				},
				idToken: token?.accessToken,
			};

			const response = await chatApi(request);
			if (!response.body) {
				throw Error('No response body');
			}
			if (shouldStream) {
				const parsedResponse: ChatAppResponse =
					await handleAsyncRequest(
						question,
						answers,
						setAnswers,
						response.body
					);

				await analytics.track('Question Replied', {
					reply: parsedResponse.choices[0].message.content,
					timestamp: Math.round(new Date().getTime() / 1000),
				});

				setAnswers([...answers, [question, parsedResponse]]);
			} else {
				const parsedResponse: ChatAppResponseOrError =
					await response.json();
				if (response.status > 299 || !response.ok) {
					throw Error(parsedResponse.error || 'Unknown error');
				}

				setAnswers([
					...answers,
					[question, parsedResponse as ChatAppResponse],
				]);
			}
		} catch (e) {
			setError(e);
		} finally {
			setIsLoading(false);
		}
	};

	const clearChat = () => {
		lastQuestionRef.current = '';
		error && setError(undefined);
		setActiveCitation(undefined);
		setActiveAnalysisPanelTab(undefined);
		setAnswers([]);
		setStreamedAnswers([]);
		setIsLoading(false);
		setIsStreaming(false);
	};

	useEffect(
		() =>
			chatMessageStreamEnd.current?.scrollIntoView({
				behavior: 'smooth',
			}),
		[isLoading]
	);
	useEffect(
		() =>
			chatMessageStreamEnd.current?.scrollIntoView({ behavior: 'auto' }),
		[streamedAnswers]
	);

	const onPromptTemplateChange = (
		_ev?: React.FormEvent<HTMLInputElement | HTMLTextAreaElement>,
		newValue?: string
	) => {
		setPromptTemplate(newValue || '');
	};

	const onRetrieveCountChange = (
		_ev?: React.SyntheticEvent<HTMLElement, Event>,
		newValue?: string
	) => {
		setRetrieveCount(parseInt(newValue || '3'));
	};

	const onRetrievalModeChange = (
		_ev: React.FormEvent<HTMLDivElement>,
		option?: IDropdownOption<RetrievalMode> | undefined,
		index?: number | undefined
	) => {
		setRetrievalMode(option?.data || RetrievalMode.Hybrid);
	};

	const onUseSemanticRankerChange = (
		_ev?: React.FormEvent<HTMLElement | HTMLInputElement>,
		checked?: boolean
	) => {
		setUseSemanticRanker(!!checked);
	};

	const onUseSemanticCaptionsChange = (
		_ev?: React.FormEvent<HTMLElement | HTMLInputElement>,
		checked?: boolean
	) => {
		setUseSemanticCaptions(!!checked);
	};

	const onShouldStreamChange = (
		_ev?: React.FormEvent<HTMLElement | HTMLInputElement>,
		checked?: boolean
	) => {
		setShouldStream(!!checked);
	};

	const onExcludeCategoryChanged = (
		_ev?: React.FormEvent,
		newValue?: string
	) => {
		setExcludeCategory(newValue || '');
	};

	const onUseSuggestFollowupQuestionsChange = (
		_ev?: React.FormEvent<HTMLElement | HTMLInputElement>,
		checked?: boolean
	) => {
		setUseSuggestFollowupQuestions(!!checked);
	};

	const onUseOidSecurityFilterChange = (
		_ev?: React.FormEvent<HTMLElement | HTMLInputElement>,
		checked?: boolean
	) => {
		setUseOidSecurityFilter(!!checked);
	};

	const onUseGroupsSecurityFilterChange = (
		_ev?: React.FormEvent<HTMLElement | HTMLInputElement>,
		checked?: boolean
	) => {
		setUseGroupsSecurityFilter(!!checked);
	};

	const onExampleClicked = (example: string) => {
		makeApiRequest(example);
	};

	const onShowCitation = (citation: string, index: number) => {
		if (
			activeCitation === citation &&
			activeAnalysisPanelTab === AnalysisPanelTabs.CitationTab &&
			selectedAnswer === index
		) {
			setActiveAnalysisPanelTab(undefined);
		} else {
			setActiveCitation(citation);
			setActiveAnalysisPanelTab(AnalysisPanelTabs.CitationTab);
		}

		setSelectedAnswer(index);
	};

	const onToggleTab = (tab: AnalysisPanelTabs, index: number) => {
		if (activeAnalysisPanelTab === tab && selectedAnswer === index) {
			setActiveAnalysisPanelTab(undefined);
		} else {
			setActiveAnalysisPanelTab(tab);
		}

		setSelectedAnswer(index);
	};

	const handleFinishedClick = async (data: {
		feedback: string;
		comment?: string;
	}) => {
		await analytics.track('Chat Completed', {
			time_to_complete: Math.round(
				(new Date().getTime() - timer.current) / 1000
			),
			results: data.feedback === 'good' ? 1 : 0,
			message: data?.comment || '',
			timestamp: Math.round(new Date().getTime() / 1000),
		});

		const lastAnswer = answers[answers.length - 1];

		await fetch('/logs/add', {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
			},
			body: JSON.stringify({
				uuid: sessionStorage.getItem('ajs_anonymous_id'),
				feedback: data?.comment || '',
				timestamp: new Date().getTime(),
				thought_process: lastAnswer[1].choices[0].extra_args.thoughts,
			}),
		});

		timer.current = 0;

		clearChat();
	};

	return (
		<Layout
			headerActions={
				<div className={styles.commandsContainer}>
					{lastQuestionRef.current && (
						<FinishChatButton
							className={styles.commandButton}
							onSubmit={handleFinishedClick}
						/>
					)}

					<SettingsButton
						className={styles.commandButton}
						onClick={() => setIsConfigPanelOpen(!isConfigPanelOpen)}
					/>
				</div>
			}>
			<div className={styles.container}>
				<div className={styles.chatRoot}>
					<div className={styles.chatContainer}>
						{!lastQuestionRef.current ? (
							<div className={styles.chatEmptyState}>
								<h2 className={styles.chatEmptyStateTitle}>
									Forslag til åpningsspørsmål
								</h2>

								<p className={styles.chatEmptyStateSubtitle}>
									Du kan også starte samtalen med egne
									spørsmål under...
								</p>

								<ExampleList
									onExampleClicked={onExampleClicked}
								/>
							</div>
						) : (
							<div className={styles.chatMessageStream}>
								{isStreaming &&
									streamedAnswers.map(
										(streamedAnswer, index) => (
											<div key={index}>
												<UserChatMessage
													message={streamedAnswer[0]}
												/>
												<div
													className={
														styles.chatMessageGpt
													}>
													<Answer
														isStreaming={true}
														key={index}
														answer={
															streamedAnswer[1]
														}
														isSelected={false}
														onCitationClicked={c =>
															onShowCitation(
																c,
																index
															)
														}
														onThoughtProcessClicked={() =>
															onToggleTab(
																AnalysisPanelTabs.ThoughtProcessTab,
																index
															)
														}
														onSupportingContentClicked={() =>
															onToggleTab(
																AnalysisPanelTabs.SupportingContentTab,
																index
															)
														}
														onFollowupQuestionClicked={q =>
															makeApiRequest(q)
														}
														showFollowupQuestions={
															useSuggestFollowupQuestions &&
															answers.length -
																1 ===
																index
														}
													/>
												</div>
											</div>
										)
									)}
								{!isStreaming &&
									answers.map((answer, index) => (
										<div key={index}>
											<UserChatMessage
												message={answer[0]}
											/>
											<div
												className={
													styles.chatMessageGpt
												}>
												<Answer
													isStreaming={false}
													key={index}
													answer={answer[1]}
													isSelected={
														selectedAnswer ===
															index &&
														activeAnalysisPanelTab !==
															undefined
													}
													onCitationClicked={c =>
														onShowCitation(c, index)
													}
													onThoughtProcessClicked={() =>
														onToggleTab(
															AnalysisPanelTabs.ThoughtProcessTab,
															index
														)
													}
													onSupportingContentClicked={() =>
														onToggleTab(
															AnalysisPanelTabs.SupportingContentTab,
															index
														)
													}
													onFollowupQuestionClicked={q =>
														makeApiRequest(q)
													}
													showFollowupQuestions={
														useSuggestFollowupQuestions &&
														answers.length - 1 ===
															index
													}
												/>
											</div>
										</div>
									))}
								{isLoading && (
									<>
										<UserChatMessage
											message={lastQuestionRef.current}
										/>
										<div
											className={
												styles.chatMessageGptMinWidth
											}>
											<AnswerLoading />
										</div>
									</>
								)}
								{error ? (
									<>
										<UserChatMessage
											message={lastQuestionRef.current}
										/>
										<div
											className={
												styles.chatMessageGptMinWidth
											}>
											<AnswerError
												error={error.toString()}
												onRetry={() =>
													makeApiRequest(
														lastQuestionRef.current
													)
												}
											/>
										</div>
									</>
								) : null}
								<div ref={chatMessageStreamEnd} />
							</div>
						)}

						<div className={styles.chatInput}>
							<ClearChatButton
								onClick={clearChat}
								disabled={!lastQuestionRef.current || isLoading}
							/>

							<QuestionInput
								clearOnSend
								placeholder="Skriv et nytt spørsmål. For eksempel “Er det bindingstid på Spotpris?”"
								disabled={isLoading}
								onSend={question => makeApiRequest(question)}
							/>
						</div>
					</div>

					{answers.length > 0 && activeAnalysisPanelTab && (
						<AnalysisPanel
							className={styles.chatAnalysisPanel}
							activeCitation={activeCitation}
							onActiveTabChanged={x =>
								onToggleTab(x, selectedAnswer)
							}
							citationHeight="810px"
							answer={answers[selectedAnswer][1]}
							activeTab={activeAnalysisPanelTab}
						/>
					)}

					<Panel
						headerText="Configure answer generation"
						isOpen={isConfigPanelOpen}
						isBlocking={false}
						onDismiss={() => setIsConfigPanelOpen(false)}
						closeButtonAriaLabel="Close"
						onRenderFooterContent={() => (
							<DefaultButton
								onClick={() => setIsConfigPanelOpen(false)}>
								Close
							</DefaultButton>
						)}
						isFooterAtBottom={true}>
						<TextField
							className={styles.chatSettingsSeparator}
							defaultValue={promptTemplate}
							label="Override prompt template"
							multiline
							autoAdjustHeight
							onChange={onPromptTemplateChange}
						/>

						<SpinButton
							className={styles.chatSettingsSeparator}
							label="Retrieve this many search results:"
							min={1}
							max={50}
							defaultValue={retrieveCount.toString()}
							onChange={onRetrieveCountChange}
						/>
						<TextField
							className={styles.chatSettingsSeparator}
							label="Exclude category"
							onChange={onExcludeCategoryChanged}
						/>
						<Checkbox
							className={styles.chatSettingsSeparator}
							checked={useSemanticRanker}
							label="Use semantic ranker for retrieval"
							onChange={onUseSemanticRankerChange}
						/>
						<Checkbox
							className={styles.chatSettingsSeparator}
							checked={useSemanticCaptions}
							label="Use query-contextual summaries instead of whole documents"
							onChange={onUseSemanticCaptionsChange}
							disabled={!useSemanticRanker}
						/>
						<Checkbox
							className={styles.chatSettingsSeparator}
							checked={useSuggestFollowupQuestions}
							label="Suggest follow-up questions"
							onChange={onUseSuggestFollowupQuestionsChange}
						/>
						{useLogin && (
							<Checkbox
								className={styles.chatSettingsSeparator}
								checked={useOidSecurityFilter}
								label="Use oid security filter"
								disabled={!client?.getActiveAccount()}
								onChange={onUseOidSecurityFilterChange}
							/>
						)}
						{useLogin && (
							<Checkbox
								className={styles.chatSettingsSeparator}
								checked={useGroupsSecurityFilter}
								label="Use groups security filter"
								disabled={!client?.getActiveAccount()}
								onChange={onUseGroupsSecurityFilterChange}
							/>
						)}
						<Dropdown
							className={styles.chatSettingsSeparator}
							label="Retrieval mode"
							options={[
								{
									key: 'hybrid',
									text: 'Vectors + Text (Hybrid)',
									selected:
										retrievalMode == RetrievalMode.Hybrid,
									data: RetrievalMode.Hybrid,
								},
								{
									key: 'vectors',
									text: 'Vectors',
									selected:
										retrievalMode == RetrievalMode.Vectors,
									data: RetrievalMode.Vectors,
								},
								{
									key: 'text',
									text: 'Text',
									selected:
										retrievalMode == RetrievalMode.Text,
									data: RetrievalMode.Text,
								},
							]}
							required
							onChange={onRetrievalModeChange}
						/>
						<Checkbox
							className={styles.chatSettingsSeparator}
							checked={shouldStream}
							label="Stream chat completion responses"
							onChange={onShouldStreamChange}
						/>
						{useLogin && <TokenClaimsDisplay />}
					</Panel>
				</div>
			</div>
		</Layout>
	);
};

export default Chat;
