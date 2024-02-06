import { useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { Button } from '@fluentui/react-components';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import {
	faCheck,
	faMessageCheck,
	faStar,
	faXmark,
} from '@fortawesome/pro-regular-svg-icons';
import { faStar as faStarSolid } from '@fortawesome/pro-solid-svg-icons';

import styles from './FinishChatButton.module.scss';

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
				icon={<FontAwesomeIcon icon={faMessageCheck} />}
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
					<FontAwesomeIcon icon={faXmark} />
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
								<FontAwesomeIcon icon={faStarSolid} />
							) : (
								<FontAwesomeIcon icon={faStar} />
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

						<FontAwesomeIcon icon={faCheck} />
					</button>
				</div>
			</div>
		</div>,
		document.getElementById('portal') as Element
	);
};
