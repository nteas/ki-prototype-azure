import DOMPurify from 'dompurify';
import { createPortal } from 'react-dom';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faXmark } from '@fortawesome/pro-regular-svg-icons';

import styles from './AnalysisPanel.module.scss';

import { SupportingContent } from '../SupportingContent';
import { ChatAppResponse } from '../../api';
import { AnalysisPanelTabs } from './AnalysisPanelTabs';

interface Props {
	activeTab: AnalysisPanelTabs;
	onActiveTabChanged: (tab: AnalysisPanelTabs) => void;
	activeCitation: string | undefined;
	citationHeight: string;
	answer: ChatAppResponse;
}

export const AnalysisPanel = ({
	answer,
	activeTab,
	activeCitation,
	citationHeight,
	onActiveTabChanged,
}: Props) => {
	const isDisabledThoughtProcessTab: boolean =
		!answer.choices[0].extra_args.thoughts;
	const isDisabledSupportingContentTab: boolean =
		!answer.choices[0].extra_args.data_points.length;
	const isDisabledCitationTab: boolean = !activeCitation;

	const sanitizedThoughts = DOMPurify.sanitize(
		answer.choices[0].extra_args.thoughts!
	);

	return createPortal(
		<div className={styles.modalWrapper}>
			<div
				className={styles.overlay}
				onClick={() => onActiveTabChanged(activeTab)}
			/>

			<div className={styles.modal}>
				<div
					className={styles.closeButtonWrap}
					onClick={() => onActiveTabChanged(activeTab)}>
					<FontAwesomeIcon icon={faXmark} />

					<span>Lukk</span>
				</div>

				<div className={styles.modalNav}>
					<button
						className={
							activeTab === AnalysisPanelTabs.ThoughtProcessTab
								? styles.activeButton
								: ''
						}
						onClick={() =>
							onActiveTabChanged(
								AnalysisPanelTabs.ThoughtProcessTab
							)
						}
						disabled={isDisabledThoughtProcessTab}>
						Tankeprosess
					</button>
					<button
						className={
							activeTab === AnalysisPanelTabs.SupportingContentTab
								? styles.activeButton
								: ''
						}
						onClick={() =>
							onActiveTabChanged(
								AnalysisPanelTabs.SupportingContentTab
							)
						}
						disabled={isDisabledSupportingContentTab}>
						Dokumentasjon
					</button>
					<button
						className={
							activeTab === AnalysisPanelTabs.CitationTab
								? styles.activeButton
								: ''
						}
						onClick={() =>
							onActiveTabChanged(AnalysisPanelTabs.CitationTab)
						}
						disabled={isDisabledCitationTab}>
						Kilder
					</button>
				</div>

				<div className={styles.content}>
					{activeTab === AnalysisPanelTabs.ThoughtProcessTab && (
						<div className={styles.tab}>
							<div
								className={styles.thoughtProcess}
								dangerouslySetInnerHTML={{
									__html: sanitizedThoughts,
								}}></div>
						</div>
					)}

					{activeTab === AnalysisPanelTabs.SupportingContentTab && (
						<div className={styles.tab}>
							<SupportingContent
								supportingContent={
									answer.choices[0].extra_args.data_points
								}
							/>
						</div>
					)}

					{activeTab === AnalysisPanelTabs.CitationTab && (
						<div className={styles.tab}>
							<iframe
								className={styles.frame}
								title="Kilde"
								src={activeCitation}
								width="100%"
								height={citationHeight}
							/>
						</div>
					)}
				</div>
			</div>
		</div>,
		document.getElementById('portal') as Element
	);
};
