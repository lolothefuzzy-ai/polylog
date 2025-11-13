"""
Bonding Operations Panel for Polylog GUI.

Provides UI controls for:
- Discovering bond candidates
- Creating and removing bonds
- Viewing bond strength and alignment scores
- Managing hinge creation
"""

from typing import Any, Dict, List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from unified_bonding_system import BondCandidate, UnifiedBondingSystem


class BondCandidateItem(QListWidgetItem):
    """List item representing a bond candidate."""
    
    def __init__(self, candidate: BondCandidate):
        self.candidate = candidate
        
        # Format display text
        text = (f"Bond: {candidate.poly1_id} (edge {candidate.edge1_idx}) ↔ "
                f"{candidate.poly2_id} (edge {candidate.edge2_idx})\n"
                f"  Score: {candidate.score:.3f} | "
                f"Distance: {candidate.distance:.2f} | "
                f"Alignment: {candidate.alignment_score:.3f}")
        
        super().__init__(text)
        
        # Color-code by quality
        if candidate.score >= 0.9:
            self.setForeground(Qt.darkGreen)
        elif candidate.score >= 0.7:
            self.setForeground(Qt.darkBlue)
        elif candidate.score >= 0.5:
            self.setForeground(Qt.darkYellow)
        else:
            self.setForeground(Qt.darkRed)


class BondingPanel(QWidget):
    """
    Panel for bond discovery and creation operations.
    
    Signals:
        discover_bonds_requested(): Request bond discovery
        create_bond_requested(dict): Request bond creation with candidate data
        remove_bond_requested(str): Request bond removal by bond_id
        bond_selected(dict): Emitted when a bond candidate is selected
    """
    
    discover_bonds_requested = Signal()
    create_bond_requested = Signal(dict)
    remove_bond_requested = Signal(str)
    bond_selected = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.bonding_system = None
        self.current_candidates: List[BondCandidate] = []
        self.selected_candidate: Optional[BondCandidate] = None
        self._setup_ui()
    
    def _setup_ui(self):
        """Build the UI layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        
        # === Bond Discovery Group ===
        discovery_group = QGroupBox("Bond Discovery")
        discovery_layout = QVBoxLayout()
        
        # Discovery controls
        controls_layout = QHBoxLayout()
        
        self.discover_btn = QPushButton("Discover Bonds")
        self.discover_btn.setToolTip("Find potential bond locations between polyforms (or press B)")
        self.discover_btn.clicked.connect(self._on_discover_clicked)
        controls_layout.addWidget(self.discover_btn)
        
        self.auto_discover_checkbox = QPushButton("Auto")
        self.auto_discover_checkbox.setCheckable(True)
        self.auto_discover_checkbox.setMaximumWidth(60)
        self.auto_discover_checkbox.setToolTip("Automatically discover bonds when assembly changes")
        controls_layout.addWidget(self.auto_discover_checkbox)
        
        discovery_layout.addLayout(controls_layout)
        
        # Discovery settings
        settings_layout = QFormLayout()
        
        self.max_candidates_spin = QSpinBox()
        self.max_candidates_spin.setRange(1, 100)
        self.max_candidates_spin.setValue(10)
        self.max_candidates_spin.setToolTip("Maximum number of bond candidates to display")
        settings_layout.addRow("Max Candidates:", self.max_candidates_spin)
        
        self.distance_threshold_spin = QDoubleSpinBox()
        self.distance_threshold_spin.setRange(0.01, 10.0)
        self.distance_threshold_spin.setValue(0.1)
        self.distance_threshold_spin.setSingleStep(0.1)
        self.distance_threshold_spin.setDecimals(2)
        self.distance_threshold_spin.setToolTip("Maximum distance between edges to consider for bonding")
        settings_layout.addRow("Distance Threshold:", self.distance_threshold_spin)
        
        discovery_layout.addLayout(settings_layout)
        
        # Progress bar
        self.discovery_progress = QProgressBar()
        self.discovery_progress.setVisible(False)
        discovery_layout.addWidget(self.discovery_progress)
        
        # Status label
        self.discovery_status = QLabel("Ready")
        self.discovery_status.setStyleSheet("color: #666; font-size: 10px;")
        discovery_layout.addWidget(self.discovery_status)
        
        discovery_group.setLayout(discovery_layout)
        layout.addWidget(discovery_group)
        
        # === Bond Candidates List ===
        candidates_group = QGroupBox("Bond Candidates")
        candidates_layout = QVBoxLayout()
        
        self.candidates_list = QListWidget()
        self.candidates_list.itemSelectionChanged.connect(self._on_candidate_selected)
        candidates_layout.addWidget(self.candidates_list)
        
        # Candidate count label
        self.candidates_count_label = QLabel("Candidates: 0")
        self.candidates_count_label.setStyleSheet("color: #666; font-size: 10px;")
        candidates_layout.addWidget(self.candidates_count_label)
        
        candidates_group.setLayout(candidates_layout)
        layout.addWidget(candidates_group, 1)
        
        # === Bond Actions ===
        actions_group = QGroupBox("Actions")
        actions_layout = QVBoxLayout()
        
        self.create_bond_btn = QPushButton("Create Bond")
        self.create_bond_btn.setToolTip("Create bond between selected polyform pair")
        self.create_bond_btn.clicked.connect(self._on_create_bond_clicked)
        self.create_bond_btn.setEnabled(False)
        actions_layout.addWidget(self.create_bond_btn)
        
        self.create_with_hinge_checkbox = QPushButton("With Hinge")
        self.create_with_hinge_checkbox.setCheckable(True)
        self.create_with_hinge_checkbox.setChecked(True)
        self.create_with_hinge_checkbox.setToolTip("Create hinge along with bond")
        actions_layout.addWidget(self.create_with_hinge_checkbox)
        
        # Advanced options
        advanced_layout = QFormLayout()
        
        self.bond_strength_spin = QDoubleSpinBox()
        self.bond_strength_spin.setRange(0.1, 2.0)
        self.bond_strength_spin.setValue(1.0)
        self.bond_strength_spin.setSingleStep(0.1)
        self.bond_strength_spin.setDecimals(1)
        advanced_layout.addRow("Bond Strength:", self.bond_strength_spin)
        
        actions_layout.addLayout(advanced_layout)
        
        actions_group.setLayout(actions_layout)
        layout.addWidget(actions_group)
        
        # === Current Bonds ===
        bonds_group = QGroupBox("Current Bonds")
        bonds_layout = QVBoxLayout()
        
        self.bonds_list = QListWidget()
        bonds_layout.addWidget(self.bonds_list)
        
        remove_bond_btn = QPushButton("Remove Selected Bond")
        remove_bond_btn.setToolTip("Remove the currently selected bond")
        remove_bond_btn.clicked.connect(self._on_remove_bond_clicked)
        bonds_layout.addWidget(remove_bond_btn)
        
        self.bonds_count_label = QLabel("Bonds: 0")
        self.bonds_count_label.setStyleSheet("color: #666; font-size: 10px;")
        bonds_layout.addWidget(self.bonds_count_label)
        
        bonds_group.setLayout(bonds_layout)
        layout.addWidget(bonds_group, 1)
        
        layout.addStretch()
    
    def set_bonding_system(self, bonding_system: UnifiedBondingSystem):
        """Set the bonding system to use."""
        self.bonding_system = bonding_system
        print("✓ Bonding system connected to GUI")
    
    def _on_discover_clicked(self):
        """Handle discover bonds button click."""
        if not self.bonding_system:
            self.discovery_status.setText("Error: No bonding system available")
            return
        
        self.discovery_status.setText("Discovering bonds...")
        self.discover_btn.setEnabled(False)
        self.discovery_progress.setVisible(True)
        self.discovery_progress.setRange(0, 0)  # Indeterminate
        
        # Emit signal - actual discovery happens in main controller
        self.discover_bonds_requested.emit()
    
    def update_candidates(self, candidates: List[BondCandidate]):
        """Update the list of bond candidates."""
        self.current_candidates = candidates
        self.candidates_list.clear()
        
        # Sort by score (best first)
        sorted_candidates = sorted(candidates, key=lambda c: c.score, reverse=True)
        
        # Limit to max_candidates setting
        max_count = self.max_candidates_spin.value()
        displayed = sorted_candidates[:max_count]
        
        for candidate in displayed:
            item = BondCandidateItem(candidate)
            self.candidates_list.addItem(item)
        
        # Update UI
        self.candidates_count_label.setText(f"Candidates: {len(candidates)} (showing {len(displayed)})")
        self.discovery_status.setText(f"Found {len(candidates)} bond candidates")
        self.discover_btn.setEnabled(True)
        self.discovery_progress.setVisible(False)
        
        print(f"✓ Updated bond candidates: {len(candidates)} found")
    
    def _on_candidate_selected(self):
        """Handle candidate selection."""
        items = self.candidates_list.selectedItems()
        if not items:
            self.create_bond_btn.setEnabled(False)
            self.selected_candidate = None
            return
        
        item = items[0]
        if isinstance(item, BondCandidateItem):
            self.selected_candidate = item.candidate
            self.create_bond_btn.setEnabled(True)
            
            # Emit selection signal for viewport visualization
            candidate_data = {
                'poly1_id': item.candidate.poly1_id,
                'edge1_idx': item.candidate.edge1_idx,
                'poly2_id': item.candidate.poly2_id,
                'edge2_idx': item.candidate.edge2_idx,
                'score': item.candidate.score
            }
            self.bond_selected.emit(candidate_data)
    
    def _on_create_bond_clicked(self):
        """Handle create bond button click."""
        if not self.selected_candidate:
            return
        
        bond_data = {
            'poly1_id': self.selected_candidate.poly1_id,
            'edge1_idx': self.selected_candidate.edge1_idx,
            'poly2_id': self.selected_candidate.poly2_id,
            'edge2_idx': self.selected_candidate.edge2_idx,
            'create_hinge': self.create_with_hinge_checkbox.isChecked(),
            'strength': self.bond_strength_spin.value()
        }
        
        self.create_bond_requested.emit(bond_data)
        self.discovery_status.setText("Bond created")
        
        print(f"✓ Created bond: {bond_data['poly1_id']} ↔ {bond_data['poly2_id']}")
    
    def _on_remove_bond_clicked(self):
        """Handle remove bond button click."""
        items = self.bonds_list.selectedItems()
        if not items:
            return
        
        item = items[0]
        bond_id = item.data(Qt.UserRole)
        if bond_id:
            self.remove_bond_requested.emit(bond_id)
            self.discovery_status.setText("Bond removed")
    
    def update_bonds_list(self, bonds: List[Dict[str, Any]]):
        """Update the list of current bonds."""
        self.bonds_list.clear()
        
        for bond in bonds:
            bond_id = bond.get('id', '?')
            poly1 = bond.get('poly1_id', '?')
            poly2 = bond.get('poly2_id', '?')
            edge1 = bond.get('edge1_idx', '?')
            edge2 = bond.get('edge2_idx', '?')
            
            text = f"{poly1} (edge {edge1}) ↔ {poly2} (edge {edge2})"
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, bond_id)
            self.bonds_list.addItem(item)
        
        self.bonds_count_label.setText(f"Bonds: {len(bonds)}")
    
    def clear(self):
        """Clear all lists and reset state."""
        self.candidates_list.clear()
        self.bonds_list.clear()
        self.current_candidates = []
        self.selected_candidate = None
        self.create_bond_btn.setEnabled(False)
        self.discovery_status.setText("Ready")
        self.candidates_count_label.setText("Candidates: 0")
        self.bonds_count_label.setText("Bonds: 0")
