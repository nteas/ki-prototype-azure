import { Pivot, PivotItem } from '@fluentui/react';
import DOMPurify from 'dompurify';
import { createPortal } from 'react-dom';
import { Dismiss24Regular } from '@fluentui/react-icons';

import styles from './AnalysisPanel.module.css';

import { SupportingContent } from '../SupportingContent';
import { ChatAppResponse } from '../../api';
import { AnalysisPanelTabs } from './AnalysisPanelTabs';

interface Props {
	className: string;
	activeTab: AnalysisPanelTabs;
	onActiveTabChanged: (tab: AnalysisPanelTabs) => void;
	activeCitation: string | undefined;
	citationHeight: string;
	answer: ChatAppResponse;
}

const pivotItemDisabledStyle = { disabled: true, style: { color: 'grey' } };

export const AnalysisPanel = ({
	answer,
	activeTab,
	activeCitation,
	citationHeight,
	className,
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
					<Dismiss24Regular />

					<span>Lukk</span>
				</div>

				<Pivot
					className={className}
					selectedKey={activeTab}
					onLinkClick={pivotItem =>
						pivotItem &&
						onActiveTabChanged(
							pivotItem.props.itemKey! as AnalysisPanelTabs
						)
					}>
					<PivotItem
						itemKey={AnalysisPanelTabs.ThoughtProcessTab}
						headerText="Tankeprosess"
						headerButtonProps={
							isDisabledThoughtProcessTab
								? pivotItemDisabledStyle
								: undefined
						}>
						<div
							className={styles.thoughtProcess}
							dangerouslySetInnerHTML={{
								__html: sanitizedThoughts,
							}}></div>
					</PivotItem>
					<PivotItem
						itemKey={AnalysisPanelTabs.SupportingContentTab}
						headerText="Dokumentasjon"
						headerButtonProps={
							isDisabledSupportingContentTab
								? pivotItemDisabledStyle
								: undefined
						}>
						<SupportingContent
							supportingContent={
								answer.choices[0].extra_args.data_points
							}
						/>
					</PivotItem>
					<PivotItem
						itemKey={AnalysisPanelTabs.CitationTab}
						headerText="Kilder"
						headerButtonProps={
							isDisabledCitationTab
								? pivotItemDisabledStyle
								: undefined
						}>
						<iframe
							title="Kilde"
							src={activeCitation}
							width="100%"
							height={citationHeight}
						/>
					</PivotItem>
				</Pivot>
			</div>
		</div>,
		document.getElementById('portal') as Element
	);
};
