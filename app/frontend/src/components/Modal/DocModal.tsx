import { useState } from 'react';
import { Button } from 'react-bootstrap';

import { Document } from '../../api';
import Modal from './Modal';

export default function DocModal({
	document,
	onClose,
}: {
	document?: Document;
	onClose: () => void;
}) {
	const [file, setFile] = useState<string | null>(null);

	return (
		<Modal onClose={onClose} title={document?.title}>
			<div
				style={{
					display: 'flex',
					flexDirection: 'column',
					gap: '10px',
					marginBottom: '24px',
				}}>
				{document?.file_pages
					?.sort((a: string, b: string) => a.localeCompare(b))
					.map((page, i) => (
						<Button key={i} onClick={() => setFile(page)}>
							{page}
						</Button>
					))}
			</div>

			{file && (
				<iframe
					style={{
						width: '100%',
						minHeight: '65vh',
						border: 'none',
					}}
					src={`/api/content/${file}`}
				/>
			)}
		</Modal>
	);
}
