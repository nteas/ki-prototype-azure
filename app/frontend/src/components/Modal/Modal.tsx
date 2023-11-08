import { createPortal } from 'react-dom';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faXmark } from '@fortawesome/pro-regular-svg-icons';

import styles from './Modal.module.css';

interface Props {
	onClose: () => void;
	title?: string;
	children: React.ReactNode;
}

const Modal = ({ onClose, title, children }: Props) => {
	return createPortal(
		<div className={styles.modalWrapper}>
			<div className={styles.overlay} onClick={onClose} />

			<div className={styles.modal}>
				<div className={styles.closeButtonWrap} onClick={onClose}>
					<FontAwesomeIcon icon={faXmark} />

					<span>Lukk</span>
				</div>

				<div className={styles.content}>
					{title && <h2>{title}</h2>}

					{children}
				</div>
			</div>
		</div>,
		document.getElementById('portal') as Element
	);
};

export default Modal;
