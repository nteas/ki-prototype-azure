import { useState } from 'react';
import { Stack, TextField } from '@fluentui/react';
import { Button } from '@fluentui/react-components';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faMagnifyingGlass } from '@fortawesome/pro-regular-svg-icons';
import { faPaperPlane } from '@fortawesome/pro-solid-svg-icons';

import styles from './QuestionInput.module.scss';

interface Props {
	onSend: (question: string) => void;
	disabled: boolean;
	placeholder?: string;
	clearOnSend?: boolean;
	search?: boolean;
}

export const QuestionInput = ({
	onSend,
	disabled,
	placeholder,
	clearOnSend,
	search = false,
}: Props) => {
	const [question, setQuestion] = useState<string>('');

	const sendQuestion = () => {
		if (disabled || !question.trim()) {
			return;
		}

		onSend(question);

		if (clearOnSend) {
			setQuestion('');
		}
	};

	const onEnterPress = (ev: React.KeyboardEvent<Element>) => {
		if (ev.key === 'Enter' && !ev.shiftKey) {
			ev.preventDefault();
			sendQuestion();
		}
	};

	const onQuestionChange = (
		_ev: React.FormEvent<HTMLInputElement | HTMLTextAreaElement>,
		newValue?: string
	) => {
		if (!newValue) {
			setQuestion('');
		} else if (newValue.length <= 1000) {
			setQuestion(newValue);
		}
	};

	const sendQuestionDisabled = disabled || !question.trim();

	return (
		<Stack horizontal className={styles.questionInputContainer}>
			<TextField
				className={styles.questionInputTextArea}
				placeholder={placeholder}
				multiline
				resizable={false}
				borderless
				value={question}
				onChange={onQuestionChange}
				onKeyDown={onEnterPress}
			/>
			<div className={styles.questionInputButtonsContainer}>
				<Button
					size="large"
					icon={
						search ? (
							<FontAwesomeIcon icon={faMagnifyingGlass} />
						) : (
							<FontAwesomeIcon icon={faPaperPlane} />
						)
					}
					disabled={sendQuestionDisabled}
					onClick={sendQuestion}
				/>
			</div>
		</Stack>
	);
};
