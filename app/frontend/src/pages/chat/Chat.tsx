import { useRef, useState, useEffect } from 'react';

import styles from './Chat.module.scss';

import {
	Answer,
	AnswerError,
	AnswerLoading,
	ChatResponse,
} from '../../components/Answer';
import { QuestionInput } from '../../components/QuestionInput';
import { ExampleList } from '../../components/Example';
import { UserChatMessage } from '../../components/UserChatMessage';
import { AnalysisPanelTabs } from '../../components/AnalysisPanel';
import { SettingsButton } from '../../components/SettingsButton';
import Layout from '../../components/Layout/Layout';
import analytics from '../../libs/analytics';
import { ClearChatButton } from '../../components/ClearChatButton';

const Chat = () => {
	const lastQuestionRef = useRef<string>('');
	const chatMessageStreamEnd = useRef<HTMLDivElement | null>(null);

	const [isLoading, setIsLoading] = useState<boolean>(false);
	const [error, setError] = useState<unknown>();
	const [activeCitation, setActiveCitation] = useState<string>();
	const [selectedAnswer, setSelectedAnswer] = useState<number>(0);
	const [answers, setAnswers] = useState<ChatResponse[]>([]);
	const [streamedAnswer, setStreamedAnswer] = useState<string>();

	const timer = useRef<number>(0);

	const makeApiRequest = async (question: string) => {
		await analytics.track('Question Asked', {
			question,
			timestamp: Math.round(new Date().getTime() / 1000),
		});

		lastQuestionRef.current = question;

		if (timer.current === 0) {
			timer.current = new Date().getTime() / 1000;
		}

		error && setError(undefined);
		setIsLoading(true);
		setActiveCitation(undefined);

		fetch('/api/chat_stream', {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
				Accepts: 'text/plain',
			},
			body: JSON.stringify({
				question,
			}),
		})
			.then(response => {
				setIsLoading(false);
				let accumulatedResponse = '';
				const reader = response.body?.getReader();
				const stream = new ReadableStream({
					start(controller) {
						reader?.read().then(function process({ done, value }) {
							if (done) {
								setAnswers(prev => [
									...prev,
									{
										user: question,
										response: accumulatedResponse || '',
									},
								]);

								analytics.track('Question Replied', {
									reply: accumulatedResponse,
									timestamp: Math.round(
										new Date().getTime() / 1000
									),
									responseTime: Math.round(
										new Date().getTime() / 1000 -
											timer.current
									),
								});

								timer.current = 0;

								setStreamedAnswer(undefined);

								setIsLoading(false);

								controller.close();
								return;
							}

							accumulatedResponse += new TextDecoder(
								'utf-8'
							).decode(value);

							setStreamedAnswer(accumulatedResponse);

							reader?.read().then(process);
						});
					},
				});

				return new Response(stream, {
					headers: { 'Content-Type': 'text/plain' },
				});
			})
			.catch(e => {
				console.error(e);
				setError(e);
			});
	};

	const clearChat = () => {
		lastQuestionRef.current = '';
		error && setError(undefined);
		setActiveCitation(undefined);
		setAnswers([]);
		setStreamedAnswer(undefined);
		setIsLoading(false);
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
		[streamedAnswer]
	);

	const onExampleClicked = (example: string) => {
		makeApiRequest(example);
	};

	const onShowCitation = (citation: string, index: number) => {
		if (activeCitation !== citation || selectedAnswer !== index) {
			setActiveCitation(citation);
		}

		setSelectedAnswer(index);
	};

	const onToggleTab = (tab: AnalysisPanelTabs, index: number) => {
		setSelectedAnswer(index);
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

					<SettingsButton className={styles.commandButton} />
				</>
			}>
			<div className={styles.chatContainer}>
				{!lastQuestionRef.current ? (
					<div className={styles.chatEmptyState}>
						<h2 className={styles.chatEmptyStateTitle}>
							Forslag til åpningsspørsmål
						</h2>

						<p className={styles.chatEmptyStateSubtitle}>
							Du kan også starte samtalen med egne spørsmål
							under...
						</p>

						<ExampleList onExampleClicked={onExampleClicked} />
					</div>
				) : (
					<div className={styles.chatMessageStream}>
						{answers?.map((answer, index) => (
							<div key={index}>
								<UserChatMessage message={answer?.user} />

								<div className={styles.chatMessageGpt}>
									<Answer
										isStreaming={false}
										key={index}
										answer={answer?.response}
										isSelected={selectedAnswer === index}
										onCitationClicked={c =>
											onShowCitation(c, index)
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
											answers.length - 1 === index
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
								<div className={styles.chatMessageGptMinWidth}>
									<AnswerLoading />
								</div>
							</>
						)}

						{streamedAnswer && (
							<>
								<UserChatMessage
									message={lastQuestionRef.current}
								/>

								<div className={styles.chatMessageGpt}>
									<Answer
										isStreaming={true}
										answer={streamedAnswer}
										isSelected={false}
									/>
								</div>
							</>
						)}

						{error ? (
							<>
								<UserChatMessage
									message={lastQuestionRef.current}
								/>
								<div className={styles.chatMessageGptMinWidth}>
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
					<QuestionInput
						clearOnSend
						placeholder="Skriv et nytt spørsmål. For eksempel “Er det bindingstid på Spotpris?”"
						disabled={isLoading}
						onSend={question => makeApiRequest(question)}
					/>
				</div>
			</div>
		</Layout>
	);
};

export default Chat;
