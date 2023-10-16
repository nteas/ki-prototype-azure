import { useMemo } from 'react';
import { IconButton } from '@fluentui/react';
import DOMPurify from 'dompurify';

import styles from './Answer.module.css';

import { ChatAppResponse, getCitationFilePath } from '../../api';
import { parseAnswerToHtml } from './AnswerParser';
import { AnswerIcon } from './AnswerIcon';

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
	const messageContent = answer.choices[0].message.content;
	const parsedAnswer = useMemo(
		() => parseAnswerToHtml(messageContent, isStreaming, onCitationClicked),
		[answer]
	);

	const sanitizedAnswerHtml = DOMPurify.sanitize(parsedAnswer.answerHtml);

	return (
		<div
			className={`${styles.answerContainer} ${
				isSelected && styles.selected
			}`}>
			<div className={styles.answerIcons}>
				<AnswerIcon />

				<div className={styles.answerActionIcons}>
					<IconButton
						iconProps={{ iconName: 'Lightbulb' }}
						title="Show thought process"
						ariaLabel="Show thought process"
						onClick={() => onThoughtProcessClicked()}
						disabled={
							!answer.choices[0].extra_args.thoughts?.length
						}
					/>
					<IconButton
						iconProps={{ iconName: 'ClipboardList' }}
						title="Show supporting content"
						ariaLabel="Show supporting content"
						onClick={() => onSupportingContentClicked()}
						disabled={
							!answer.choices[0].extra_args.data_points?.length
						}
					/>
				</div>
			</div>

			<div
				className={styles.answerText}
				dangerouslySetInnerHTML={{
					__html: sanitizedAnswerHtml,
				}}></div>

			{!!parsedAnswer.citations.length && (
				<div className={styles.citations}>
					<span className={styles.citationLearnMore}>Kilder:</span>

					{parsedAnswer.citations.map((x, i) => {
						const path = getCitationFilePath(x);
						return (
							<a
								key={i}
								className={styles.citation}
								title={x}
								onClick={() => onCitationClicked(path)}>
								{`${++i}. ${x}`}
							</a>
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
		</div>
	);
};
