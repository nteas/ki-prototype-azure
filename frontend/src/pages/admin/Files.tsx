import { useEffect, useState } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faFilePdf } from '@fortawesome/pro-solid-svg-icons';

import AdminLayout from '../../components/Layout/AdminLayout';
import styles from './Admin.module.scss';
import { apiFetch, File } from '../../api';

export function Component(): JSX.Element {
	const [loading, setLoading] = useState<boolean>(true);
	const [files, setFiles] = useState<[File]>();

	useEffect(() => {
		apiFetch('/api/file-index')
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
	}, []);

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
				{files?.map(item => <ItemRow key={item.title} item={item} />) ??
					[]}
			</div>
		</AdminLayout>
	);
}

Component.displayName = 'Files';

function ItemRow({ item }: { item: File }) {
	return (
		<div
			className={styles.row}
			key={item.title}
			style={{ cursor: 'pointer' }}
			onClick={() => {
				window.open(item.url, '_blank');
			}}>
			<div className={styles.col} style={{ flex: 1 }}>
				<FontAwesomeIcon icon={faFilePdf} />
			</div>

			<div className={styles.col} style={{ flex: '0 1 95%' }}>
				{item.title}
			</div>
		</div>
	);
}
