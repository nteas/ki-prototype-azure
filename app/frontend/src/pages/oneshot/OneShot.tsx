import { useRef, useState } from 'react';
import {
	Checkbox,
	Panel,
	DefaultButton,
	Spinner,
	TextField,
	SpinButton,
	IDropdownOption,
	Dropdown,
} from '@fluentui/react';

import styles from './OneShot.module.css';

import {
	askApi,
	ChatAppResponse,
	AskRequest,
	RetrievalMode,
	// logChat,
} from '../../api';
import { Answer, AnswerError } from '../../components/Answer';
import { QuestionInput } from '../../components/QuestionInput';
import {
	AnalysisPanel,
	AnalysisPanelTabs,
} from '../../components/AnalysisPanel';
import { SettingsButton } from '../../components/SettingsButton/SettingsButton';
import { useLogin, getToken } from '../../authConfig';
import { useMsal } from '@azure/msal-react';
import { TokenClaimsDisplay } from '../../components/TokenClaimsDisplay';
import Layout from '../../components/Layout/Layout';
import analytics from '../../libs/analytics';
import { ClearChatButton } from '../../components/ClearChatButton';

export function Component(): JSX.Element {
	const [isConfigPanelOpen, setIsConfigPanelOpen] = useState(false);
	const [promptTemplate, setPromptTemplate] = useState<string>('');
	const [promptTemplatePrefix, setPromptTemplatePrefix] =
		useState<string>('');
	const [promptTemplateSuffix, setPromptTemplateSuffix] =
		useState<string>('');
	const [retrievalMode, setRetrievalMode] = useState<RetrievalMode>(
		RetrievalMode.Hybrid
	);
	const [retrieveCount, setRetrieveCount] = useState<number>(3);
	const [useSemanticRanker, setUseSemanticRanker] = useState<boolean>(true);
	const [useSemanticCaptions, setUseSemanticCaptions] =
		useState<boolean>(false);
	const [excludeCategory, setExcludeCategory] = useState<string>('');
	const [useOidSecurityFilter, setUseOidSecurityFilter] =
		useState<boolean>(false);
	const [useGroupsSecurityFilter, setUseGroupsSecurityFilter] =
		useState<boolean>(false);

	const timer = useRef<number>(0);
	// const questionCounter = useRef<number>(0);
	const lastQuestionRef = useRef<string>('');

	const [isLoading, setIsLoading] = useState<boolean>(false);
	const [error, setError] = useState<unknown>();
	const [answer, setAnswer] = useState<ChatAppResponse>();

	const [activeCitation, setActiveCitation] = useState<string>();
	const [activeAnalysisPanelTab, setActiveAnalysisPanelTab] = useState<
		AnalysisPanelTabs | undefined
	>(undefined);

	const client = useLogin ? useMsal().instance : undefined;

	const makeApiRequest = async (question: string) => {
		await analytics.track('Question Asked', {
			question,
			timestamp: Math.round(new Date().getTime() / 1000),
		});

		if (timer.current === 0) {
			timer.current = new Date().getTime() / 1000;
		}

		lastQuestionRef.current = question;

		error && setError(undefined);
		setIsLoading(true);
		setActiveCitation(undefined);
		setActiveAnalysisPanelTab(undefined);

		const token = client ? await getToken(client) : undefined;

		try {
			const request: AskRequest = {
				question,
				overrides: {
					promptTemplate:
						promptTemplate.length === 0
							? undefined
							: promptTemplate,
					promptTemplatePrefix:
						promptTemplatePrefix.length === 0
							? undefined
							: promptTemplatePrefix,
					promptTemplateSuffix:
						promptTemplateSuffix.length === 0
							? undefined
							: promptTemplateSuffix,
					excludeCategory:
						excludeCategory.length === 0
							? undefined
							: excludeCategory,
					top: retrieveCount,
					retrievalMode: retrievalMode,
					semanticRanker: useSemanticRanker,
					semanticCaptions: useSemanticCaptions,
					useOidSecurityFilter: useOidSecurityFilter,
					useGroupsSecurityFilter: useGroupsSecurityFilter,
				},
				idToken: token?.accessToken,
			};
			const result = await askApi(request);

			await analytics.track('Question Replied', {
				reply: result.choices[0].message.content,
				timestamp: Math.round(new Date().getTime() / 1000),
				responseTime: Math.round(
					new Date().getTime() / 1000 - timer.current
				),
			});

			timer.current = 0;

			setAnswer(result);
		} catch (e) {
			setError(e);
		} finally {
			setIsLoading(false);
		}
	};

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

	const onExcludeCategoryChanged = (
		_ev?: React.FormEvent,
		newValue?: string
	) => {
		setExcludeCategory(newValue || '');
	};

	const onShowCitation = (citation: string) => {
		if (
			activeCitation === citation &&
			activeAnalysisPanelTab === AnalysisPanelTabs.CitationTab
		) {
			setActiveAnalysisPanelTab(undefined);
		} else {
			setActiveCitation(citation);
			setActiveAnalysisPanelTab(AnalysisPanelTabs.CitationTab);
		}
	};

	const onToggleTab = (tab: AnalysisPanelTabs) => {
		if (activeAnalysisPanelTab === tab) {
			setActiveAnalysisPanelTab(undefined);
		} else {
			setActiveAnalysisPanelTab(tab);
		}
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

	// const handleFinishedClick = async (data: {
	// 	feedback: number;
	// 	comment?: string;
	// }) => {
	// 	await logChat({
	// 		feedback: data.feedback,
	// 		comment: data.comment || '',
	// 		thought_process: answer?.choices[0].extra_args.thoughts || '',
	// 	});

	// 	clearChat();
	// };

	const clearChat = () => {
		lastQuestionRef.current = '';
		error && setError(undefined);
		setActiveCitation(undefined);
		setActiveAnalysisPanelTab(undefined);
		setAnswer(undefined);
	};

	return (
		<Layout
			headerActions={
				<>
					{lastQuestionRef.current && (
						<ClearChatButton
							className={styles.commandButton}
							onClick={clearChat}
						/>
					)}

					<SettingsButton
						className={styles.settingsButton}
						onClick={() => setIsConfigPanelOpen(!isConfigPanelOpen)}
					/>
				</>
			}>
			<div className={styles.oneshotContainer}>
				<div className={styles.oneshotTopSection}>
					<h2 className={styles.oneshotTitle}>
						Søk i spørsmål og svar
					</h2>

					<p className={styles.oneshotSubTitle}>
						Boten vil kun søke i alle FAQ-innleggene på nte.no
					</p>

					<div className={styles.oneshotQuestionInput}>
						<QuestionInput
							placeholder="Skriv et nytt spørsmål. For eksempel “Er det bindingstid på Spotpris?”"
							disabled={isLoading}
							onSend={question => makeApiRequest(question)}
							search
						/>
					</div>
				</div>
				<div className={styles.oneshotBottomSection}>
					{isLoading && <Spinner label="Genererer svar" />}

					{!isLoading && answer && !error && (
						<div className={styles.oneshotAnswerContainer}>
							<Answer
								answer={answer}
								isStreaming={false}
								onCitationClicked={x => onShowCitation(x)}
								onThoughtProcessClicked={() =>
									onToggleTab(
										AnalysisPanelTabs.ThoughtProcessTab
									)
								}
								onSupportingContentClicked={() =>
									onToggleTab(
										AnalysisPanelTabs.SupportingContentTab
									)
								}
							/>
						</div>
					)}
					{error ? (
						<div className={styles.oneshotAnswerContainer}>
							<AnswerError
								error={error.toString()}
								onRetry={() =>
									makeApiRequest(lastQuestionRef.current)
								}
							/>
						</div>
					) : null}
					{activeAnalysisPanelTab && answer && (
						<AnalysisPanel
							className={styles.oneshotAnalysisPanel}
							activeCitation={activeCitation}
							onActiveTabChanged={x => onToggleTab(x)}
							citationHeight="600px"
							answer={answer}
							activeTab={activeAnalysisPanelTab}
						/>
					)}
				</div>

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
						className={styles.oneshotSettingsSeparator}
						defaultValue={promptTemplate}
						label="Override prompt template"
						multiline
						autoAdjustHeight
						onChange={onPromptTemplateChange}
					/>

					<SpinButton
						className={styles.oneshotSettingsSeparator}
						label="Retrieve this many search results:"
						min={1}
						max={50}
						defaultValue={retrieveCount.toString()}
						onChange={onRetrieveCountChange}
					/>
					<TextField
						className={styles.oneshotSettingsSeparator}
						label="Exclude category"
						onChange={onExcludeCategoryChanged}
					/>
					<Checkbox
						className={styles.oneshotSettingsSeparator}
						checked={useSemanticRanker}
						label="Use semantic ranker for retrieval"
						onChange={onUseSemanticRankerChange}
					/>
					<Checkbox
						className={styles.oneshotSettingsSeparator}
						checked={useSemanticCaptions}
						label="Use query-contextual summaries instead of whole documents"
						onChange={onUseSemanticCaptionsChange}
						disabled={!useSemanticRanker}
					/>
					{useLogin && (
						<Checkbox
							className={styles.oneshotSettingsSeparator}
							checked={useOidSecurityFilter}
							label="Use oid security filter"
							disabled={!client?.getActiveAccount()}
							onChange={onUseOidSecurityFilterChange}
						/>
					)}
					{useLogin && (
						<Checkbox
							className={styles.oneshotSettingsSeparator}
							checked={useGroupsSecurityFilter}
							label="Use groups security filter"
							disabled={!client?.getActiveAccount()}
							onChange={onUseGroupsSecurityFilterChange}
						/>
					)}
					<Dropdown
						className={styles.oneshotSettingsSeparator}
						label="Retrieval mode"
						options={[
							{
								key: 'hybrid',
								text: 'Vectors + Text (Hybrid)',
								selected: retrievalMode == RetrievalMode.Hybrid,
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
								selected: retrievalMode == RetrievalMode.Text,
								data: RetrievalMode.Text,
							},
						]}
						required
						onChange={onRetrievalModeChange}
					/>
					{useLogin && <TokenClaimsDisplay />}
				</Panel>
			</div>
		</Layout>
	);
}

Component.displayName = 'OneShot';
