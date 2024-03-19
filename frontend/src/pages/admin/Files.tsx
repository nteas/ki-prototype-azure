import { useEffect, useState } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faFilePdf, faFlag, faEye } from '@fortawesome/pro-solid-svg-icons';

import AdminLayout from '../../components/Layout/AdminLayout';
import styles from './Admin.module.scss';
import { apiFetch, File } from '../../api';

export function Component(): JSX.Element {
	const [loading, setLoading] = useState<boolean>(false);
	const [files, setFiles] = useState<[File]>();

	useEffect(() => {
		getFiles();
	}, []);

	const getFiles = () => {
		setLoading(true);
		setFiles(undefined);
		apiFetch('/api/files/')
			.then(res => res.json())
			.then(data => {
				setFiles(data.files);
			})
			.catch(err => {
				console.error(err);
				return [];
			})
			.finally(() => {
				setLoading(false);
			});
	};

	const handleUnflagItem = (title: string) => {
		apiFetch('/api/files/unflag', {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
			},
			body: JSON.stringify({ title }),
		}).then(getFiles);
	};

	return (
		<AdminLayout
			className={styles.layout}
			loading={loading}
			breadcrumbs={[
				{
					link: '#',
					text: 'Indekserte filer',
				},
			]}>
			<h2 className={styles.title}>Indekserte filer</h2>

			<p>Viser {files?.length} indekserte filer.</p>

			<div className={styles.rows}>
				{files?.map(item => (
					<ItemRow
						key={item.title}
						item={item}
						handleUnflagItem={() => handleUnflagItem(item.title)}
					/>
				)) ?? []}
			</div>
		</AdminLayout>
	);
}

Component.displayName = 'Files';

function ItemRow({
	item,
	handleUnflagItem,
}: {
	item: File;
	handleUnflagItem: () => void;
}) {
	return (
		<div
			className={`${styles.row} ${item?.flagged && styles.flagged}`}
			key={item.title}
			style={{ cursor: 'pointer' }}>
			<div className={styles.col} style={{ flex: 1 }}>
				<FontAwesomeIcon icon={faFilePdf} />
			</div>

			<div className={styles.col} style={{ flex: '0 1 90%' }}>
				{item.title}
			</div>

			<div
				className={`${styles.col} ${styles.actions}`}
				style={{ flex: 2 }}>
				{item.flagged && (
					<button
						className={styles.delete}
						onClick={() => handleUnflagItem()}
						title="Slett">
						<FontAwesomeIcon icon={faFlag} />
					</button>
				)}

				<button
					className={styles.open}
					onClick={() => window.open(item.url, '_blank')}
					title="Åpne">
					<FontAwesomeIcon icon={faEye} />
				</button>
			</div>
		</div>
	);
}
