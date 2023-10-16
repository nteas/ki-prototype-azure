import { useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import {
	CommentCheckmark24Regular,
	Checkmark24Regular,
	Star48Regular,
	Star48Filled,
	Dismiss24Regular,
} from '@fluentui/react-icons';
import { Button } from '@fluentui/react-components';

import styles from './FinishChatButton.module.css';

interface Props {
	className?: string;
	disabled?: boolean;
	onSubmit: (data: { feedback: number; comment?: string }) => Promise<void>;
}

export const FinishChatButton = ({ className, disabled, onSubmit }: Props) => {
	const [open, setOpen] = useState(false);

	return (
		<div className={`${styles.container} ${className ?? ''}`}>
			<Button
				icon={<CommentCheckmark24Regular />}
				disabled={disabled}
				onClick={() => setOpen(true)}>
				Fullfør
			</Button>

			{open && (
				<Modal onClose={() => setOpen(false)} onSubmit={onSubmit} />
			)}
		</div>
	);
};

interface ModalProps {
	onClose: () => void;
	onSubmit: (data: { feedback: number; comment?: string }) => Promise<void>;
}

const Modal = ({ onClose, onSubmit }: ModalProps) => {
	const [valid, setValid] = useState(false);
	const [feedback, setFeedback] = useState(0);
	const commentRef = useRef<HTMLTextAreaElement>(null);

	const handleSubmit = async () => {
		await onSubmit({
			feedback,
			comment: commentRef?.current?.value || undefined,
		});

		onClose();
	};

	return createPortal(
		<div className={styles.modalWrapper}>
			<div className={styles.overlay} onClick={onClose} />

			<div className={styles.modal}>
				<button className={styles.closeButton} onClick={onClose}>
					<Dismiss24Regular />
				</button>

				<h2>Fullfør samtale</h2>

				<p>
					Gi oss en tommel opp eller ned på om verktøyet hjalp deg å
					behandle kunden eller ikke. Kommentar er valgfritt.
				</p>

				<div className={styles.feedbackButtons}>
					{[1, 2, 3, 4, 5].map(i => (
						<button
							key={i}
							className={`${styles.button} ${
								feedback >= i
									? styles.successButton
									: styles.warningButton
							}`}
							onClick={() => {
								setFeedback(i);
								setValid(i > 0);
							}}>
							{feedback >= i ? (
								<Star48Filled />
							) : (
								<Star48Regular />
							)}
						</button>
					))}
				</div>

				<textarea ref={commentRef} placeholder="Valgfri kommentar" />

				<div className={styles.modalActions}>
					<button
						className={`${styles.button} ${styles.outlinedButton}`}
						onClick={onClose}>
						Avbryt
					</button>

					<button
						className={`${styles.button}`}
						disabled={!valid}
						onClick={handleSubmit}>
						<span>Fullfør og start ny samtale</span>

						<Checkmark24Regular />
					</button>
				</div>
			</div>
		</div>,
		document.getElementById('portal') as Element
	);
};
