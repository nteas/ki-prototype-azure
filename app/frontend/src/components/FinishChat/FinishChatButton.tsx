import { useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import {
	CommentCheckmark24Regular,
	Checkmark24Regular,
	ThumbLike24Regular,
	ThumbDislike24Regular,
} from '@fluentui/react-icons';
import { Button } from '@fluentui/react-components';

import styles from './FinishChatButton.module.css';

interface Props {
	className?: string;
	disabled?: boolean;
	onSubmit: (data: { feedback: string; comment?: string }) => Promise<void>;
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
	onSubmit: (data: { feedback: string; comment?: string }) => Promise<void>;
}

const Modal = ({ onClose, onSubmit }: ModalProps) => {
	const [valid, setValid] = useState(false);
	const [successClicked, setSuccessClicked] = useState(false);
	const [warningClicked, setWarningClicked] = useState(false);
	const commentRef = useRef<HTMLTextAreaElement>(null);

	const handleSubmit = async () => {
		await onSubmit({
			feedback: successClicked ? 'good' : 'bad',
			comment: commentRef?.current?.value || undefined,
		});

		onClose();
	};

	return createPortal(
		<div className={styles.modalWrapper}>
			<div className={styles.overlay} onClick={onClose} />

			<div className={styles.modal}>
				<button className={styles.closeButton} onClick={onClose}>
					X
				</button>

				<h2>Fullfør samtale</h2>

				<p>
					Gi oss en tommel opp eller ned på om verktøyet hjalp deg å
					behandle kunden eller ikke. Kommentar er valgfritt.
				</p>

				<div className={styles.feedbackButtons}>
					<button
						className={`${styles.button} ${styles.successButton} ${
							successClicked && styles.successButtonActive
						}`}
						onClick={() => {
							setSuccessClicked(!successClicked);
							setWarningClicked(false);
							setValid(!successClicked);
						}}>
						<span>Bra</span>

						<ThumbLike24Regular />
					</button>

					<button
						className={`${styles.button} ${styles.warningButton} ${
							warningClicked && styles.warningButtonActive
						}`}
						onClick={() => {
							setWarningClicked(!warningClicked);
							setSuccessClicked(false);
							setValid(!warningClicked);
						}}>
						<span>Dårlig</span>

						<ThumbDislike24Regular />
					</button>
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
