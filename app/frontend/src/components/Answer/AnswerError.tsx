import { Stack, PrimaryButton } from '@fluentui/react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faExclamationCircle } from '@fortawesome/pro-solid-svg-icons';

import styles from './Answer.module.css';

interface Props {
	error: string;
	onRetry: () => void;
}

export const AnswerError = ({ error, onRetry }: Props) => {
	return (
		<Stack className={styles.answerContainer} verticalAlign="space-between">
			<FontAwesomeIcon icon={faExclamationCircle} />

			<Stack.Item grow>
				<p className={styles.answerText}>{error}</p>
			</Stack.Item>

			<PrimaryButton
				className={styles.retryButton}
				onClick={onRetry}
				text="Prøv igjen"
			/>
		</Stack>
	);
};
