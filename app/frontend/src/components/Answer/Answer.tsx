import { useEffect, useMemo, useRef, useState } from 'react';
import { Input } from '@fluentui/react-components';
import DOMPurify from 'dompurify';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import {
	faFlag,
	faStars,
	faStar as faStarSolid,
} from '@fortawesome/pro-solid-svg-icons';
import {
	faFlag as flagOutline,
	faClipboard,
	faLightbulb,
	faStar,
} from '@fortawesome/pro-regular-svg-icons';

import styles from './Answer.module.css';

import { ChatAppResponse, apiFetch, getCitationFilePath } from '../../api';
import { parseAnswerToHtml } from './AnswerParser';
import analytics from '../../libs/analytics';

interface Props {
	answer: ChatAppResponse;
	isSelected?: boolean;
	isStreaming: boolean;
	onCitationClicked: (filePath: string) => void;
	onThoughtProcessClicked: () => void;
	onSupportingContentClicked: () => void;
	onFollowupQuestionClicked?: (question: string) => void;
	showFollowupQuestions?: boolean;
}

export const Answer = ({
	answer,
	isSelected,
	isStreaming,
	onCitationClicked,
	onThoughtProcessClicked,
	onSupportingContentClicked,
	onFollowupQuestionClicked,
	showFollowupQuestions,
}: Props) => {
	const [feedback, setFeedback] = useState(0);
	const [flaggedCitations, setFlaggedCitations] = useState<string[]>([]);
	const isFeedbackGiven = useRef<boolean>(false);
	const messageContent = answer.choices[0].message.content;
	const parsedAnswer = useMemo(
		() => parseAnswerToHtml(messageContent, isStreaming, onCitationClicked),
		[answer]
	);

	const sanitizedAnswerHtml = DOMPurify.sanitize(parsedAnswer.answerHtml);

	function updateFlaggedCitations(citation: string) {
		if (flaggedCitations.includes(citation)) {
			setFlaggedCitations(prev => prev.filter(x => x !== citation));
		} else {
			setFlaggedCitations(prev => [...prev, citation]);
		}
	}

	async function flagCitations(message: string) {
		return await apiFetch('/api/documents/flag', {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
			},
			body: JSON.stringify({ citations: flaggedCitations, message }),
		});
	}

	return (
		<div
			className={`${styles.answerContainer} ${
				isSelected && styles.selected
			}`}>
			<div className={styles.answerIcons}>
				<FontAwesomeIcon icon={faStars} />

				<div className={styles.answerActionIcons}>
					<button
						className={styles.answerActionIcon}
						title="Show thought process"
						onClick={() => onThoughtProcessClicked()}
						disabled={
							!answer.choices[0].extra_args.thoughts?.length
						}>
						<FontAwesomeIcon icon={faLightbulb} />
					</button>

					<button
						className={styles.answerActionIcon}
						title="Show supporting content"
						onClick={() => onSupportingContentClicked()}
						disabled={
							!answer.choices[0].extra_args.data_points?.length
						}>
						<FontAwesomeIcon icon={faClipboard} />
					</button>
				</div>
			</div>

			<div
				className={styles.answerText}
				dangerouslySetInnerHTML={{
					__html: sanitizedAnswerHtml
						.replace(/\n /g, '<br/>&nbsp;')
						.replace(/\n/g, '<br/>'),
				}}></div>

			{!!parsedAnswer.citations.length && (
				<div className={styles.citations}>
					<span className={styles.citationLearnMore}>Kilder:</span>

					{parsedAnswer.citations.map((x, i) => {
						const path = getCitationFilePath(x);
						return (
							<Citation
								key={i}
								index={i}
								citation={x}
								onCitationClick={() => onCitationClicked(path)}
								updateFlags={() => updateFlaggedCitations(x)}
								isFlagged={flaggedCitations.includes(x)}
								isFeedbackGiven={isFeedbackGiven}
							/>
						);
					})}
				</div>
			)}

			{!!parsedAnswer.followupQuestions.length &&
				showFollowupQuestions &&
				onFollowupQuestionClicked && (
					<>
						<span className={styles.followupQuestionLearnMore}>
							Follow-up questions:
						</span>

						{parsedAnswer.followupQuestions.map((x, i) => {
							return (
								<a
									key={i}
									className={styles.followupQuestion}
									title={x}
									onClick={() =>
										onFollowupQuestionClicked(x)
									}>
									{`${x}`}
								</a>
							);
						})}
					</>
				)}

			{!isFeedbackGiven.current && (
				<div className={styles.feedbackWrapper}>
					<div className={styles.feedbackButtons}>
						{[1, 2, 3, 4, 5].map(i => (
							<button
								key={i}
								className={`${styles.button} ${
									feedback >= i && styles.activeButton
								}`}
								onClick={() => {
									setFeedback(i);
								}}>
								{feedback >= i ? (
									<FontAwesomeIcon icon={faStarSolid} />
								) : (
									<FontAwesomeIcon icon={faStar} />
								)}
							</button>
						))}
					</div>

					{(feedback > 0 || flaggedCitations?.length > 0) && (
						<form
							className={styles.form}
							onSubmit={async (
								e: React.FormEvent<HTMLFormElement>
							) => {
								e.preventDefault();

								analytics.track('Feedback Given', {
									answer: messageContent,
									result:
										feedback === 0
											? 'not_specified'
											: feedback,
									comment: e?.currentTarget?.comment?.value,
								});

								if (flaggedCitations?.length > 0) {
									await flagCitations(
										e?.currentTarget?.comment?.value
									);
								}

								isFeedbackGiven.current = true;

								setFeedback(0);
								e.currentTarget.comment.value = '';
							}}>
							<div className={styles.inputWrapper}>
								<Input
									name="comment"
									placeholder="Skriv en kommentar"
								/>
							</div>

							<button
								className={`${styles.button} ${styles.submitButton}`}
								type="submit">
								Send
							</button>
						</form>
					)}
				</div>
			)}
		</div>
	);
};

interface CitationProps {
	index: number;
	citation: string;
	onCitationClick: () => void;
	updateFlags: (citation: string) => void;
	isFlagged: boolean;
	isFeedbackGiven: React.MutableRefObject<boolean>;
}

function Citation({
	index,
	citation,
	onCitationClick,
	updateFlags,
	isFlagged,
	isFeedbackGiven,
}: CitationProps) {
	useEffect(() => {
		if (isFlagged) return;

		apiFetch(`/api/documents/flag/${citation}`)
			.then(res => res.json())
			.then(res => {
				if (!res.flagged) return;
				isFeedbackGiven.current = true;
				updateFlags(citation);
			})
			.catch(err => console.error(err));
	}, []);

	return (
		<div className={styles.citationWrapper}>
			<button
				className={styles.citation}
				title={citation}
				onClick={onCitationClick}>
				{`${++index}. ${citation}`}
			</button>

			<button
				className={`${styles.citationFlag} ${
					isFlagged && styles.citationFlagged
				}`}
				onClick={() => updateFlags(citation)}
				disabled={isFeedbackGiven.current}>
				<FontAwesomeIcon icon={isFlagged ? faFlag : flagOutline} />
			</button>
		</div>
	);
}
