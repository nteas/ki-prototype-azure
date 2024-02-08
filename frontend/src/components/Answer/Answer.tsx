import { useEffect, useMemo, useRef, useState } from 'react';
import Form from 'react-bootstrap/Form';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import {
	faFlag,
	faStars,
	faStar as faStarSolid,
} from '@fortawesome/pro-solid-svg-icons';
import {
	faFlag as flagOutline,
	faClipboard,
	faStar,
} from '@fortawesome/pro-regular-svg-icons';

import styles from './Answer.module.scss';

import { apiFetch } from '../../api';
import { parseAnswerToHtml } from './AnswerParser';
import analytics from '../../libs/analytics';

export interface ChatResponse {
	user: string;
	response: string;
}

interface Props {
	answer: string;
	isSelected?: boolean;
	isStreaming: boolean;
	onCitationClicked?: (filePath: string) => void;
	onSupportingContentClicked?: () => void;
	onFollowupQuestionClicked?: (question: string) => void;
	showFollowupQuestions?: boolean;
}

export const Answer = ({
	answer,
	isSelected,
	isStreaming,
	onCitationClicked = () => {},
	onSupportingContentClicked,
	onFollowupQuestionClicked,
	showFollowupQuestions,
}: Props) => {
	const [feedback, setFeedback] = useState(0);
	const [flaggedCitations, setFlaggedCitations] = useState<string[]>([]);
	const isFeedbackGiven = useRef<boolean>(false);
	const commentRef = useRef<HTMLInputElement>(null);
	const messageContent = answer;
	const parsedAnswer = useMemo(
		() => parseAnswerToHtml(messageContent, isStreaming, onCitationClicked),
		[answer]
	);

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
						title="Show supporting content"
						onClick={
							onSupportingContentClicked
								? () => onSupportingContentClicked()
								: undefined
						}
						disabled={!answer?.length}>
						<FontAwesomeIcon icon={faClipboard} />
					</button>
				</div>
			</div>

			<div
				className={styles.answerText}
				dangerouslySetInnerHTML={{
					__html: parsedAnswer.answerHtml,
				}}></div>

			{!!parsedAnswer.citations.length && (
				<div className={styles.citations}>
					<span className={styles.citationLearnMore}>Kilder:</span>

					{parsedAnswer.citations.map((x, i) => {
						return (
							<Citation
								key={i}
								index={i}
								citation={x}
								onCitationClick={() => window.open(x, '_blank')}
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
									source: 'bot-kundesenter',
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
								if (commentRef.current) {
									commentRef.current.value = '';
								}

								isFeedbackGiven.current = true;

								setFeedback(0);
							}}>
							<div className={styles.inputWrapper}>
								<Form.Control
									ref={commentRef}
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
	citation: any;
	onCitationClick: () => void;
	updateFlags: (citation: any) => void;
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
	const isFlagChecked = useRef<boolean>(false);

	useEffect(() => {
		if (isFlagged || isFlagChecked.current) return;

		apiFetch(`/api/documents/flag/?citation=${citation}`)
			.then(res => res.json())
			.then(res => {
				isFlagChecked.current = true;
				if (!res.flagged) return;
				isFeedbackGiven.current = true;
				updateFlags(citation);
			})
			.catch(err => console.error(err));
	}, []);

	const isDocument = citation.split('/').pop().includes('.');
	const url = new URL(citation);

	const label = isDocument
		? decodeURIComponent(url.pathname.split('/').pop() ?? '')
		: citation.startsWith('http')
		? citation.split('//').pop().split('/')[0]
		: citation;

	return (
		<div
			className={`${styles.citationWrapper} ${
				isDocument && styles.citationWrapperDoc
			}`}>
			<button
				className={styles.citation}
				title={label}
				onClick={onCitationClick}>
				{`${++index}. ${label}`}
			</button>

			{!isDocument && (
				<button
					className={`${styles.citationFlag} ${
						isFlagged && styles.citationFlagged
					}`}
					onClick={() => updateFlags(citation)}
					disabled={isFeedbackGiven.current}>
					<FontAwesomeIcon icon={isFlagged ? faFlag : flagOutline} />
				</button>
			)}
		</div>
	);
}
