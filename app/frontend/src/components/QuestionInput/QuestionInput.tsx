import { useState } from 'react';
import { Stack, TextField } from '@fluentui/react';
import { Button, Tooltip } from '@fluentui/react-components';
import { Send28Filled, Search28Filled } from '@fluentui/react-icons';

import styles from './QuestionInput.module.css';

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
				<Tooltip content="Ask question button" relationship="label">
					<Button
						size="large"
						icon={search ? <Search28Filled /> : <Send28Filled />}
						disabled={sendQuestionDisabled}
						onClick={sendQuestion}
						className={
							search ? styles.searchButton : styles.sendButton
						}
					/>
				</Tooltip>
			</div>
		</Stack>
	);
};
