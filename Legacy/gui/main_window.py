"""
Main application window for Polylog Simulator GUI.

Implements the core window layout with:
- Menu bar and toolbar
- 3D viewport (center)
- Control panels (right side)
- Status bar

Phase 1: Foundation structure with basic layout and signal/slot connections.
"""

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QAction, QIcon, QKeySequence, QShortcut
from PySide6.QtWidgets import QHBoxLayout, QLabel, QMainWindow, QMessageBox, QPushButton, QToolBar, QVBoxLayout, QWidget

from collision_validator import CollisionValidator

# Backend systems
from generator_protocol import get_generator_registry
from gui.panels.bonding_panel import BondingPanel
from gui.panels.controls_panel import ControlsPanel
from gui.panels.generator_panel import GeneratorPanel
from gui.panels.library_panel import LibraryPanel
from gui.theme import apply_theme
from gui.viewport import Viewport3D
from hinge_manager import HingeManager
from stable_library import StableLibrary
from unified_bonding_system import UnifiedBondingSystem


class MainWindow(QMainWindow):
    """
    Main application window for Polylog Simulator.
    
    Manages the overall layout and coordinates between components.
    """
    
    # Signals for communication between components
    polygon_parameters_changed = Signal(dict)
    add_polygon_requested = Signal()
    place_polygon_requested = Signal()
    explore_requested = Signal()
    undo_requested = Signal()
    save_requested = Signal()
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Polylog Simulator - Interactive Polyform Design v0.2.0")
        self.setWindowIcon(QIcon())  # Will add icon later
        
        # Set window properties
        self.setGeometry(100, 100, 1600, 900)
        self.setMinimumSize(1400, 700)
        
        # Initialize backend systems
        self._init_backend()
        
        # Initialize components
        self._init_central_widget()
        self._init_menu_bar()
        self._init_toolbar()
        self._init_status_bar()
        self._init_keyboard_shortcuts()
        self._setup_connections()
        
        # Apply theme
        apply_theme(self)
        
        print("✓ Main window initialized with integrated systems")
    
    def _init_backend(self):
        """Initialize backend systems (assembly, generators, bonding)."""
        # Create mock assembly (simplified version for GUI)
        class SimpleAssembly:
            def __init__(self):
                self.polyforms = {}
                self.bonds = []
                self.hinge_manager = None  # Will be set if needed
            
            def add_polyform(self, poly):
                # Normalize incoming polyform when possible to ensure canonical schema
                try:
                    from gui.polyform_adapter import normalize_polyform
                    norm = normalize_polyform(poly)
                except Exception:
                    # Minimal fallback normalization
                    norm = dict(poly)
                    if 'id' not in norm:
                        norm['id'] = f'poly_{len(self.polyforms)}'
                    verts = []
                    for v in norm.get('vertices', []):
                        if isinstance(v, (list, tuple)):
                            if len(v) == 2:
                                verts.append((float(v[0]), float(v[1]), 0.0))
                            else:
                                verts.append((float(v[0]), float(v[1]), float(v[2]) if len(v) > 2 else 0.0))
                    if verts:
                        norm['vertices'] = verts

                self.polyforms[norm['id']] = norm
                return norm['id']
            
            def get_polyform(self, poly_id):
                return self.polyforms.get(poly_id)
            
            def get_all_polyforms(self):
                return list(self.polyforms.values())
            
            def get_bonds(self):
                return self.bonds
            
            def add_bond(self, bond):
                self.bonds.append(bond)
        
        self.assembly = SimpleAssembly()
        
        # Initialize generator registry
        self.generator_registry = get_generator_registry()
        self.current_generator = None
        
        # Initialize bonding system
        self.bonding_system = UnifiedBondingSystem()
        
        # Initialize hinge and validation systems
        self.hinge_manager = HingeManager()
        self.collision_validator = CollisionValidator()
        self.stable_library = StableLibrary('stable_polyforms.jsonl')
        
        # Link hinge manager to assembly
        self.assembly.hinge_manager = self.hinge_manager
        
        # Statistics tracking
        self.generation_count = 0
        self.bond_count = 0
        self.validation_enabled = True  # Enable validation by default
        
        print("✓ Backend systems initialized (with validation and library)")
    
    def _init_central_widget(self):
        """Initialize the central widget with viewport and control panels."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 3D Viewport (75% of width)
        self.viewport = Viewport3D()
        main_layout.addWidget(self.viewport, 3)
        
        # Control panels (25% of width)
        panels_widget = QWidget()
        panels_layout = QVBoxLayout(panels_widget)
        panels_layout.setContentsMargins(5, 5, 5, 5)
        panels_layout.setSpacing(5)
        
        # Generator panel (new unified system)
        self.generator_panel = GeneratorPanel()
        panels_layout.addWidget(self.generator_panel)
        
        # Bonding panel (new unified system)
        self.bonding_panel = BondingPanel()
        panels_layout.addWidget(self.bonding_panel)
        
        # Controls panel (polygon sliders - legacy)
        self.controls_panel = ControlsPanel()
        panels_layout.addWidget(self.controls_panel)
        
        # Library panel (scrollable list)
        self.library_panel = LibraryPanel()
        panels_layout.addWidget(self.library_panel, 1)
        
        main_layout.addWidget(panels_widget, 1)
        
        central_widget.setLayout(main_layout)
        
        print("✓ Central widget initialized with integrated panels")
    
    def _init_menu_bar(self):
        """Initialize the menu bar with File, Edit, View, Tools, Help."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        new_action = QAction("&New Assembly", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self._on_new_assembly)
        file_menu.addAction(new_action)
        
        file_menu.addSeparator()
        
        load_action = QAction("&Load Assembly", self)
        load_action.setShortcut("Ctrl+O")
        load_action.triggered.connect(self._on_load_assembly)
        file_menu.addAction(load_action)
        
        save_action = QAction("&Save Assembly", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self._on_save_assembly)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        
        undo_action = QAction("&Undo", self)
        undo_action.setShortcut("Ctrl+Z")
        undo_action.triggered.connect(self._on_undo)
        edit_menu.addAction(undo_action)
        
        redo_action = QAction("&Redo", self)
        redo_action.setShortcut("Ctrl+Y")
        redo_action.triggered.connect(self._on_redo)
        edit_menu.addAction(redo_action)
        
        # View menu
        view_menu = menubar.addMenu("&View")
        
        reset_view_action = QAction("&Reset View", self)
        reset_view_action.setShortcut("Home")
        reset_view_action.triggered.connect(self._on_reset_view)
        view_menu.addAction(reset_view_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("&Tools")
        
        explore_action = QAction("&Explore Mode", self)
        explore_action.setShortcut("E")
        explore_action.triggered.connect(self._on_explore)
        tools_menu.addAction(explore_action)
        
        tools_menu.addSeparator()
        
        # Validation options
        validate_assembly_action = QAction("&Validate Assembly", self)
        validate_assembly_action.setShortcut("Ctrl+T")
        validate_assembly_action.triggered.connect(self._on_validate_assembly)
        tools_menu.addAction(validate_assembly_action)
        
        self.toggle_validation_action = QAction("Enable &Validation", self)
        self.toggle_validation_action.setCheckable(True)
        self.toggle_validation_action.setChecked(True)
        self.toggle_validation_action.triggered.connect(self._on_toggle_validation)
        tools_menu.addAction(self.toggle_validation_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("&About Polylog", self)
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)
        
        print("✓ Menu bar initialized")
    
    def _init_toolbar(self):
        """Initialize the main toolbar with action buttons."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)
        
        # New button
        new_btn = QPushButton("New")
        new_btn.setToolTip("Create new assembly (Ctrl+N)")
        new_btn.clicked.connect(self._on_new_assembly)
        toolbar.addWidget(new_btn)
        
        # Place button
        place_btn = QPushButton("Place")
        place_btn.setToolTip("Place selected polygon (P)")
        place_btn.clicked.connect(self._on_place_polygon)
        toolbar.addWidget(place_btn)
        
        # Explore button
        explore_btn = QPushButton("Explore")
        explore_btn.setToolTip("Start autonomous exploration (E)")
        explore_btn.clicked.connect(self._on_explore)
        toolbar.addWidget(explore_btn)
        
        toolbar.addSeparator()
        
        # Undo button
        undo_btn = QPushButton("Undo")
        undo_btn.setToolTip("Undo last action (Ctrl+Z)")
        undo_btn.clicked.connect(self._on_undo)
        toolbar.addWidget(undo_btn)
        
        toolbar.addSeparator()
        
        # Save button
        save_btn = QPushButton("Save")
        save_btn.setToolTip("Save assembly (Ctrl+S)")
        save_btn.clicked.connect(self._on_save_assembly)
        toolbar.addWidget(save_btn)
        
        # Help button
        help_btn = QPushButton("?")
        help_btn.setToolTip("Show help")
        help_btn.clicked.connect(self._on_about)
        help_btn.setMaximumWidth(40)
        toolbar.addWidget(help_btn)
        
        print("✓ Toolbar initialized")
    
    def _init_status_bar(self):
        """Initialize the status bar with status information."""
        status_bar = self.statusBar()
        
        # Status label
        self.status_label = QLabel("Ready")
        status_bar.addWidget(self.status_label, 1)
        
        # Polyforms count
        self.polyforms_label = QLabel("Polyforms: 0")
        status_bar.addPermanentWidget(self.polyforms_label)
        
        # Success rate
        self.success_label = QLabel("Success: 0%")
        status_bar.addPermanentWidget(self.success_label)
        
        # Animation progress
        self.progress_label = QLabel("0%")
        status_bar.addPermanentWidget(self.progress_label)
        
        print("✓ Status bar initialized")
    
    def _init_keyboard_shortcuts(self):
        """Initialize keyboard shortcuts for common operations."""
        # === File Operations ===
        # Ctrl+N (New) - already in menu
        # Ctrl+O (Load) - already in menu
        # Ctrl+S (Save) - already in menu
        # Ctrl+Q (Quit) - already in menu
        
        # === Edit Operations ===
        # Ctrl+Z (Undo) - already in menu
        # Ctrl+Y (Redo) - already in menu
        
        # Delete selected polygon
        delete_shortcut = QShortcut(QKeySequence(Qt.Key_Delete), self)
        delete_shortcut.activated.connect(self._on_delete_selected)
        
        # === View Operations ===
        # Home (Reset View) - already in menu
        
        # Toggle 3D mode
        toggle_3d_shortcut = QShortcut(QKeySequence("3"), self)
        toggle_3d_shortcut.activated.connect(self._on_toggle_3d_mode)
        
        # Focus on viewport
        focus_viewport_shortcut = QShortcut(QKeySequence("F"), self)
        focus_viewport_shortcut.activated.connect(self._on_focus_viewport)
        
        # === Generation Operations ===
        # G - Generate with current settings
        generate_shortcut = QShortcut(QKeySequence("G"), self)
        generate_shortcut.activated.connect(self._on_quick_generate)
        
        # P - Place polygon
        place_shortcut = QShortcut(QKeySequence("P"), self)
        place_shortcut.activated.connect(self._on_place_polygon)
        
        # E - Explore mode (already in menu)
        
        # === Bonding Operations ===
        # B - Discover bonds
        bond_shortcut = QShortcut(QKeySequence("B"), self)
        bond_shortcut.activated.connect(self._on_discover_bonds)
        
        # === Selection Operations ===
        # Escape - Deselect all
        escape_shortcut = QShortcut(QKeySequence(Qt.Key_Escape), self)
        escape_shortcut.activated.connect(self._on_deselect_all)
        
        # Tab - Select next polygon
        tab_shortcut = QShortcut(QKeySequence(Qt.Key_Tab), self)
        tab_shortcut.activated.connect(self._on_select_next)
        
        # Shift+Tab - Select previous polygon
        shift_tab_shortcut = QShortcut(QKeySequence(Qt.ShiftModifier | Qt.Key_Tab), self)
        shift_tab_shortcut.activated.connect(self._on_select_previous)
        
        # === Number Keys for Quick Actions ===
        # 1-9 - Quick generate polygon with N sides
        for n in range(3, 10):  # 3-9 sides
            key = n - 3 + Qt.Key_3  # Map to keys 3-9
            shortcut = QShortcut(QKeySequence(key), self)
            # Use lambda with default argument to capture current value of n
            shortcut.activated.connect(lambda sides=n: self._on_quick_generate_sides(sides))
        
        # === Camera Controls ===
        # Arrow keys for camera rotation
        up_shortcut = QShortcut(QKeySequence(Qt.Key_Up), self)
        up_shortcut.activated.connect(lambda: self._on_camera_rotate(0, 10))
        
        down_shortcut = QShortcut(QKeySequence(Qt.Key_Down), self)
        down_shortcut.activated.connect(lambda: self._on_camera_rotate(0, -10))
        
        left_shortcut = QShortcut(QKeySequence(Qt.Key_Left), self)
        left_shortcut.activated.connect(lambda: self._on_camera_rotate(-10, 0))
        
        right_shortcut = QShortcut(QKeySequence(Qt.Key_Right), self)
        right_shortcut.activated.connect(lambda: self._on_camera_rotate(10, 0))
        
        # +/- for zoom
        zoom_in_shortcut = QShortcut(QKeySequence(Qt.Key_Plus), self)
        zoom_in_shortcut.activated.connect(lambda: self._on_camera_zoom(0.9))
        
        zoom_out_shortcut = QShortcut(QKeySequence(Qt.Key_Minus), self)
        zoom_out_shortcut.activated.connect(lambda: self._on_camera_zoom(1.1))
        
        # === Help ===
        # F1 - Show help
        help_shortcut = QShortcut(QKeySequence(Qt.Key_F1), self)
        help_shortcut.activated.connect(self._on_show_shortcuts_help)
        
        print("✓ Keyboard shortcuts initialized")
    
    def _setup_connections(self):
        """Connect signals between components."""
        # === Generator Panel Connections ===
        self.generator_panel.generator_selected.connect(self._on_generator_selected)
        self.generator_panel.generate_requested.connect(self._on_generate_requested)
        self.generator_panel.mode_3d_toggled.connect(self._on_3d_mode_toggled)
        
        # === Bonding Panel Connections ===
        self.bonding_panel.discover_bonds_requested.connect(self._on_discover_bonds)
        self.bonding_panel.create_bond_requested.connect(self._on_create_bond)
        self.bonding_panel.remove_bond_requested.connect(self._on_remove_bond)
        self.bonding_panel.bond_selected.connect(self._on_bond_selected)
        
        # Set bonding system reference
        self.bonding_panel.set_bonding_system(self.bonding_system)
        
        # === Legacy Controls Panel Connections ===
        self.controls_panel.parameters_changed.connect(self._on_parameters_changed)
        self.controls_panel.add_polygon_clicked.connect(self._on_add_polygon)
        self.controls_panel.polygon_generated.connect(self._on_polygon_generated)
        self.controls_panel.clear_requested.connect(self._on_clear_viewport)
        
        # === Library Panel Connections ===
        self.library_panel.design_double_clicked.connect(self._on_library_design_double_clicked)
        self.library_panel.design_selected.connect(self._update_status)
        
        # === Viewport Connections ===
        self.viewport.status_changed.connect(self._update_status)
        self.viewport.polyforms_updated.connect(self._update_polyforms_count)
        self.viewport.polygon_dropped.connect(self._on_polygon_dropped_in_viewport)
        
        print("✓ Signal/slot connections established (integrated systems)")
    
    # Slot handlers for menu/toolbar actions
    
    def _on_new_assembly(self):
        """Handle new assembly creation."""
        self.status_label.setText("Creating new assembly...")
        self.viewport.clear()
        self.status_label.setText("Ready")
        self.add_polygon_requested.emit()
    
    def _on_load_assembly(self):
        """Handle assembly loading from StableLibrary."""
        try:
            # Get list of saved assemblies
            entries = self.stable_library.list_entries()
            
            if not entries:
                QMessageBox.information(self, "No Saved Assemblies", 
                                      "No assemblies found in library.\n\nSave an assembly first using Ctrl+S.")
                return
            
            # Create selection dialog
            from PySide6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QListWidget, QVBoxLayout
            
            dialog = QDialog(self)
            dialog.setWindowTitle("Load Assembly")
            dialog.setMinimumWidth(400)
            dialog.setMinimumHeight(300)
            
            layout = QVBoxLayout(dialog)
            layout.addWidget(QLabel("Select an assembly to load:"))
            
            list_widget = QListWidget()
            for entry in sorted(entries, key=lambda e: e.get('ts', 0), reverse=True):
                import datetime
                ts = entry.get('ts', 0)
                dt = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M')
                name = entry.get('name', 'Unnamed')
                n = entry.get('n', 0)
                item_text = f"{name} ({n} polyforms) - {dt}"
                list_widget.addItem(item_text)
                list_widget.item(list_widget.count() - 1).setData(Qt.UserRole, entry['id'])
            
            layout.addWidget(list_widget)
            
            buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)
            layout.addWidget(buttons)
            
            if dialog.exec() == QDialog.Accepted and list_widget.currentItem():
                entry_id = list_widget.currentItem().data(Qt.UserRole)
                self._load_assembly_by_id(entry_id)
            
        except Exception as e:
            self.status_label.setText(f"Load error: {e}")
            print(f"❌ Load error: {e}")
            import traceback
            traceback.print_exc()
    
    def _on_save_assembly(self):
        """Handle assembly saving to StableLibrary."""
        try:
            polyforms = self.assembly.get_all_polyforms()
            
            if not polyforms:
                QMessageBox.warning(self, "Nothing to Save", 
                                  "No polyforms in assembly.\n\nGenerate some polyforms first.")
                return
            
            # Prompt for name
            from PySide6.QtWidgets import QInputDialog
            
            name, ok = QInputDialog.getText(self, "Save Assembly", 
                                          "Enter a name for this assembly:",
                                          text=f"Assembly_{len(polyforms)}_polyforms")
            
            if ok and name:
                # Save to library with hinge data
                entry_id = self.stable_library.save_assembly(
                    self.assembly, 
                    name=name,
                    meta={
                        'polyform_count': len(polyforms),
                        'bond_count': len(self.assembly.get_bonds()),
                        'validation_enabled': self.validation_enabled
                    },
                    hinge_manager=self.hinge_manager
                )
                
                self.status_label.setText(f"Assembly saved: {name}")
                QMessageBox.information(self, "Assembly Saved", 
                                      f"✓ Assembly saved successfully!\n\nName: {name}\nPolyforms: {len(polyforms)}\nID: {entry_id[:8]}...")
                
                print(f"✓ Assembly saved: {name} (ID: {entry_id})")
                self.save_requested.emit()
            
        except Exception as e:
            self.status_label.setText(f"Save error: {e}")
            print(f"❌ Save error: {e}")
            import traceback
            traceback.print_exc()
    
    def _on_undo(self):
        """Handle undo action."""
        self.viewport.undo()
        self.undo_requested.emit()
    
    def _on_redo(self):
        """Handle redo action."""
        self.viewport.redo()
    
    def _on_reset_view(self):
        """Handle view reset."""
        self.viewport.reset_view()
        self.status_label.setText("View reset")
    
    def _on_place_polygon(self):
        """Handle polygon placement."""
        self.place_polygon_requested.emit()
        self.status_label.setText("Placing polygon...")
    
    def _on_explore(self):
        """Handle exploration mode."""
        # TODO: Implement continuous exploration engine integration
        self.status_label.setText("Exploration mode coming soon")
        self.explore_requested.emit()
    
    def _on_add_polygon(self):
        """Handle add polygon from controls panel."""
        # Get current parameters and generate polygon
        params = self.controls_panel.get_parameters()
        self.polygon_parameters_changed.emit(params)
        self.add_polygon_requested.emit()
    
    def _on_polygon_generated(self, polygon_data: dict):
        """Handle polygon generation from controls panel."""
        try:
            # Add polygon to viewport
            self.viewport.add_polygon(polygon_data)
            
            # Update status
            sides = polygon_data.get('sides', '?')
            self.status_label.setText(f"Added {sides}-sided polygon")
        except Exception as e:
            self.status_label.setText(f"Error: {str(e)}")
            print(f"❌ Polygon generation error: {e}")
    
    def _on_clear_viewport(self):
        """Clear all polygons from viewport."""
        self.viewport.clear()
        self.status_label.setText("Viewport cleared")
    
    def _on_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About Polylog Simulator",
            "Polylog Simulator v0.1.0\n\n"
            "Interactive polyform design and exploration tool.\n\n"
            "Use sliders to generate polygons, place them in the assembly,\n"
            "and watch the simulator autonomously arrange them.\n\n"
            "© 2024 Polylog Team"
        )
    
    def _on_parameters_changed(self, params: dict):
        """Handle polygon parameter changes."""
        self.polygon_parameters_changed.emit(params)
        self.viewport.update_preview(params)
    
    def _update_status(self, status: str):
        """Update status bar label."""
        self.status_label.setText(status)
    
    def _update_polyforms_count(self, count: int):
        """Update polyforms count in status bar."""
        self.polyforms_label.setText(f"Polyforms: {count}")
    
    # === New Integrated System Handlers ===
    
    def _on_generator_selected(self, gen_name: str):
        """Handle generator selection from generator panel."""
        try:
            gen_class = self.generator_registry.get(gen_name)
            if gen_class:
                # Create generator instance
                enable_3d = self.generator_panel.is_3d_mode()
                self.current_generator = gen_class(self.assembly, enable_3d_mode=enable_3d)
                self.status_label.setText(f"Generator selected: {gen_name}")
                print(f"✓ Generator {gen_name} instantiated (3D: {enable_3d})")
            else:
                self.status_label.setText(f"Generator not found: {gen_name}")
        except Exception as e:
            self.status_label.setText(f"Error selecting generator: {e}")
            print(f"❌ Generator selection error: {e}")
    
    def _on_generate_requested(self, params: dict):
        """Handle generation request from generator panel."""
        if not self.current_generator:
            self.status_label.setText("No generator selected")
            return
        
        try:
            self.status_label.setText("Generating polyforms...")
            
            # Generate polyforms
            poly_ids = self.current_generator.generate(**params)
            
            # Update GUI
            self.generation_count += len(poly_ids)
            polyform_count = len(self.assembly.get_all_polyforms())
            self.polyforms_label.setText(f"Polyforms: {polyform_count}")
            
            # Update statistics in panel
            stats = self.current_generator.get_stats()
            self.generator_panel.update_statistics(stats)
            
            self.status_label.setText(f"Generated {len(poly_ids)} polyforms")
            print(f"✓ Generated {len(poly_ids)} polyforms: {poly_ids}")
            
            # Update viewport with new polyforms
            self._update_viewport_from_assembly()
            
        except Exception as e:
            self.status_label.setText(f"Generation error: {e}")
            print(f"❌ Generation error: {e}")
            import traceback
            traceback.print_exc()
    
    def _on_3d_mode_toggled(self, enabled: bool):
        """Handle 3D mode toggle."""
        self.status_label.setText(f"3D mode: {'enabled' if enabled else 'disabled'}")
        
        # Update current generator if exists
        if self.current_generator:
            self.current_generator.set_3d_mode(enabled)
        
        # TODO: Update viewport 3D rendering mode
        print(f"✓ 3D mode: {enabled}")
    
    def _on_discover_bonds(self):
        """Handle bond discovery request."""
        try:
            self.status_label.setText("Discovering bonds...")
            
            # Get all polyforms from assembly
            polyforms = self.assembly.get_all_polyforms()
            
            if len(polyforms) < 2:
                self.status_label.setText("Need at least 2 polyforms to discover bonds")
                self.bonding_panel.update_candidates([])
                return
            
            # Discover bond candidates
            candidates = self.bonding_system.discover_bonds(self.assembly)
            
            # Update bonding panel
            self.bonding_panel.update_candidates(candidates)
            
            self.status_label.setText(f"Found {len(candidates)} bond candidates")
            print(f"✓ Discovered {len(candidates)} bond candidates")
            
        except Exception as e:
            self.status_label.setText(f"Bond discovery error: {e}")
            print(f"❌ Bond discovery error: {e}")
            import traceback
            traceback.print_exc()
    
    def _on_create_bond(self, bond_data: dict):
        """Handle bond creation request."""
        try:
            self.status_label.setText("Creating bond...")
            
            # Validate bond before creation if validation is enabled
            if self.validation_enabled:
                validation_result = self._validate_bond_creation(bond_data)
                if not validation_result['valid']:
                    self.status_label.setText(f"Bond validation failed: {validation_result['reason']}")
                    QMessageBox.warning(self, "Bond Validation Failed", 
                                      f"Cannot create bond:\n{validation_result['reason']}")
                    return
            
            # Create bond using bonding system
            bond = self.bonding_system.create_bond(
                bond_data['poly1_id'],
                bond_data['edge1_idx'],
                bond_data['poly2_id'],
                bond_data['edge2_idx'],
                self.assembly,
                create_hinge=bond_data.get('create_hinge', False)
            )
            
            if bond:
                self.bond_count += 1
                
                # Create hinge for fold validation
                if bond_data.get('create_hinge', False):
                    hinge_idx = self.hinge_manager.add_bond_as_hinge(bond, self.assembly)
                    if hinge_idx is not None:
                        print(f"✓ Hinge created at index {hinge_idx}")
                
                self.status_label.setText(f"Bond created (total: {self.bond_count})")
                
                # Update bonds list
                self.bonding_panel.update_bonds_list(self.assembly.get_bonds())
                
                # Update viewport to show changes
                self._update_viewport_from_assembly()
                
                print(f"✓ Bond created: {bond_data['poly1_id']} ↔ {bond_data['poly2_id']}")
            else:
                self.status_label.setText("Failed to create bond")
        
        except Exception as e:
            self.status_label.setText(f"Bond creation error: {e}")
            print(f"❌ Bond creation error: {e}")
            import traceback
            traceback.print_exc()
    
    def _on_remove_bond(self, bond_id: str):
        """Handle bond removal request."""
        try:
            # Find and remove bond
            bonds = self.assembly.get_bonds()
            self.assembly.bonds = [b for b in bonds if b.get('id') != bond_id]
            
            self.bond_count = len(self.assembly.bonds)
            self.status_label.setText(f"Bond removed (remaining: {self.bond_count})")
            
            # Update bonds list
            self.bonding_panel.update_bonds_list(self.assembly.get_bonds())
            
            print(f"✓ Bond removed: {bond_id}")
        
        except Exception as e:
            self.status_label.setText(f"Bond removal error: {e}")
            print(f"❌ Bond removal error: {e}")
    
    def _on_bond_selected(self, bond_data: dict):
        """Handle bond candidate selection for preview."""
        # TODO: Highlight selected bond candidate in viewport
        self.status_label.setText(
            f"Selected bond: {bond_data['poly1_id']} ↔ {bond_data['poly2_id']} "
            f"(score: {bond_data['score']:.3f})"
        )
    
    def _on_library_design_double_clicked(self, design_name: str):
        """Handle double-click on library item - add to viewport."""
        try:
            # Create polygon from library design
            polygon_data = self.viewport._create_polygon_from_design(design_name, self.viewport.width() // 2, self.viewport.height() // 2)
            
            if polygon_data:
                self.viewport.add_polygon(polygon_data)
                self.status_label.setText(f"Added '{design_name}' polygon to viewport")
                print(f"✓ Added polygon from library: {design_name}")
        except Exception as e:
            self.status_label.setText(f"Error adding polygon: {e}")
            print(f"❌ Error adding polygon: {e}")
    
    def _on_polygon_dropped_in_viewport(self, polygon_data: dict):
        """Handle polygon dropped into viewport from library."""
        # Log the drop event
        print(f"✓ Polygon dropped: {polygon_data.get('name', 'Unknown')}")
    
    def _on_delete_selected(self):
        """Handle delete key - remove selected polygon."""
        if self.viewport.selected_polygon is not None:
            self.viewport.delete_polygon(self.viewport.selected_polygon)
            self.status_label.setText("Polygon deleted")
        else:
            self.status_label.setText("No polygon selected to delete")
    
    def _load_assembly_by_id(self, entry_id: str):
        """Load assembly from library by ID."""
        try:
            assembly_data = self.stable_library.get_entry(entry_id)
            if assembly_data:
                # Clear current viewport
                self.viewport.clear()
                
                # Load polygons into viewport
                if 'polyforms' in assembly_data:
                    for polyform in assembly_data['polyforms']:
                        self.viewport.add_polygon(polyform)
                
                # Clear undo/redo stacks after load
                self.viewport.undo_stack.clear()
                self.viewport.redo_stack.clear()
                
                poly_count = len(assembly_data.get('polyforms', []))
                self.status_label.setText(f"Assembly loaded: {assembly_data.get('name', 'Unknown')} ({poly_count} polygons)")
                print(f"✓ Assembly loaded: {entry_id}")
            else:
                self.status_label.setText("Failed to load assembly")
        except Exception as e:
            self.status_label.setText(f"Load error: {e}")
            print(f"❌ Load error: {e}")
    
    def _update_viewport_from_assembly(self):
        """Update viewport to show all polygons from assembly."""
        try:
            self.viewport.clear()
            polyforms = self.assembly.get_all_polyforms()
            for polyform in polyforms:
                self.viewport.add_polygon(polyform)
        except Exception as e:
            print(f"❌ Viewport update error: {e}")
    
    def _validate_bond_creation(self, bond_data: dict) -> dict:
        """Validate if a bond can be created."""
        try:
            # Check if polyforms exist
            poly1 = self.assembly.get_polyform(bond_data['poly1_id'])
            poly2 = self.assembly.get_polyform(bond_data['poly2_id'])
            
            if not poly1 or not poly2:
                return {'valid': False, 'reason': 'One or both polyforms not found'}
            
            # Check if edges exist
            if bond_data['edge1_idx'] >= len(poly1.get('edges', [])):
                return {'valid': False, 'reason': f"Edge {bond_data['edge1_idx']} not found on polyform 1"}
            
            if bond_data['edge2_idx'] >= len(poly2.get('edges', [])):
                return {'valid': False, 'reason': f"Edge {bond_data['edge2_idx']} not found on polyform 2"}
            
            return {'valid': True}
        except Exception as e:
            return {'valid': False, 'reason': str(e)}
    
    def _on_deselect_all(self):
        """Deselect all polygons."""
        self.viewport.deselect_polygon()
        self.status_label.setText("Deselected")
    
    def _on_select_next(self):
        """Select next polygon."""
        if not self.viewport.polygons:
            return
        
        current = self.viewport.selected_polygon
        if current is None:
            self.viewport.select_polygon(0)
        elif current < len(self.viewport.polygons) - 1:
            self.viewport.select_polygon(current + 1)
        else:
            self.viewport.select_polygon(0)  # Wrap around
    
    def _on_select_previous(self):
        """Select previous polygon."""
        if not self.viewport.polygons:
            return
        
        current = self.viewport.selected_polygon
        if current is None:
            self.viewport.select_polygon(len(self.viewport.polygons) - 1)
        elif current > 0:
            self.viewport.select_polygon(current - 1)
        else:
            self.viewport.select_polygon(len(self.viewport.polygons) - 1)  # Wrap around
    
    def _on_quick_generate(self):
        """Generate with current settings."""
        if self.generator_panel:
            self.generator_panel._on_generate_clicked()
    
    def _on_quick_generate_sides(self, sides: int):
        """Quick generate polygon with specified sides."""
        self.controls_panel.sides_display.setValue(sides)
        self._on_add_polygon()
    
    def _on_camera_rotate(self, dx: float, dy: float):
        """Rotate camera by delta angles."""
        self.viewport.camera_angle_y += dx
        self.viewport.camera_angle_x += dy
        self.viewport.camera_angle_x = max(-89, min(89, self.viewport.camera_angle_x))
        self.viewport.update()
    
    def _on_camera_zoom(self, factor: float):
        """Zoom camera by factor."""
        self.viewport.camera_distance *= factor
        self.viewport.camera_distance = max(1.0, min(50.0, self.viewport.camera_distance))
        self.viewport.update()
    
    def _on_toggle_3d_mode(self):
        """Toggle 3D mode."""
        if self.generator_panel:
            current = self.generator_panel.is_3d_mode()
            self.generator_panel.set_3d_mode(not current)
    
    def _on_focus_viewport(self):
        """Focus on viewport."""
        self.viewport.setFocus()
        self.status_label.setText("Viewport focused")
    
    def _on_show_shortcuts_help(self):
        """Show keyboard shortcuts help dialog."""
        from PySide6.QtWidgets import QDialog, QLabel, QScrollArea, QVBoxLayout
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Keyboard Shortcuts")
        dialog.setMinimumSize(500, 400)
        
        layout = QVBoxLayout(dialog)
        
        shortcuts_text = """
        <h3>Keyboard Shortcuts</h3>
        <b>File Operations:</b>
        • Ctrl+N - New Assembly
        • Ctrl+O - Load Assembly
        • Ctrl+S - Save Assembly
        • Ctrl+Q - Quit
        
        <b>Edit Operations:</b>
        • Ctrl+Z - Undo
        • Ctrl+Y - Redo
        • Delete - Delete Selected Polygon
        • Escape - Deselect All
        • Tab - Select Next Polygon
        • Shift+Tab - Select Previous Polygon
        
        <b>View Operations:</b>
        • Home - Reset View
        • Arrow Keys - Rotate Camera
        • +/- - Zoom In/Out
        • F - Focus Viewport
        • 3 - Toggle 3D Mode
        
        <b>Generation & Design:</b>
        • G - Generate with Current Settings
        • P - Place Polygon
        • 3-9 - Quick Generate N-sided Polygon
        • E - Exploration Mode
        • B - Discover Bonds
        
        <b>Help:</b>
        • F1 - Show This Dialog
        """
        
        scroll = QScrollArea()
        label = QLabel(shortcuts_text)
        label.setTextFormat(label.RichText)
        scroll.setWidget(label)
        layout.addWidget(scroll)
        
        dialog.exec()
    
    def _update_viewport_from_assembly(self):
        """Update viewport to display all polyforms from assembly."""
        try:
            # Get all polyforms from assembly
            polyforms = self.assembly.get_all_polyforms()
            
            # Clear viewport
            self.viewport.clear()
            
            # Add each polyform to viewport
            for poly in polyforms:
                # Convert polyform to viewport format
                viewport_data = self._convert_polyform_to_viewport(poly)
                if viewport_data:
                    self.viewport.add_polygon(viewport_data)
            
            print(f"✓ Updated viewport with {len(polyforms)} polyforms")
            
        except Exception as e:
            print(f"❌ Error updating viewport: {e}")
            import traceback
            traceback.print_exc()
    
    def _convert_polyform_to_viewport(self, polyform: dict) -> dict:
        """Convert polyform from assembly format to viewport format."""
        try:
            from gui.polyform_adapter import normalize_polyform
            
            # Normalize the polyform data
            normalized = normalize_polyform(polyform)
            
            # Create viewport-compatible polygon data
            viewport_data = {
                'name': f"Polyform {normalized['id']}",
                'vertices': normalized['vertices'],
                'sides': normalized['sides'],
                'position': normalized['position'],
                'id': normalized['id'],
                'type': normalized['type'],
                'bonds': normalized['bonds']
            }
            
            # Include 3D mesh data if available in original
            if polyform.get('has_3d_mesh') and polyform.get('mesh'):
                viewport_data['mesh'] = polyform['mesh']
                viewport_data['has_3d_mesh'] = True
            
            return viewport_data
            
        except Exception as e:
            print(f"❌ Error converting polyform: {e}")
            return None
    
    # === Keyboard Shortcut Handlers ===
    
    def _on_delete_selected(self):
        """Delete currently selected polygon (Delete key)."""
        if self.viewport.selected_polygon is not None:
            idx = self.viewport.selected_polygon
            if 0 <= idx < len(self.viewport.polygons):
                self.viewport.polygons.pop(idx)
                self.viewport.polygon_count = len(self.viewport.polygons)
                self.viewport.selected_polygon = None
                self.viewport.polyforms_updated.emit(self.viewport.polygon_count)
                self.viewport.update()
                self.status_label.setText("Polygon deleted")
    
    def _on_toggle_3d_mode(self):
        """Toggle 3D mode (3 key)."""
        current = self.generator_panel.is_3d_mode()
        self.generator_panel.mode_3d_checkbox.setChecked(not current)
        self.status_label.setText(f"3D mode: {'ON' if not current else 'OFF'}")
    
    def _on_focus_viewport(self):
        """Focus on viewport and reset view (F key)."""
        self.viewport.setFocus()
        self.viewport.reset_view()
        self.status_label.setText("Viewport focused and view reset")
    
    def _on_quick_generate(self):
        """Quick generate with current settings (G key)."""
        if self.current_generator:
            params = self.generator_panel.get_parameters()
            self.generator_panel.generate_requested.emit(params)
        else:
            self.status_label.setText("No generator selected - use generator panel")
    
    def _on_deselect_all(self):
        """Deselect all polygons (Escape key)."""
        self.viewport.deselect_polygon()
        self.status_label.setText("Selection cleared")
    
    def _on_select_next(self):
        """Select next polygon (Tab key)."""
        if not self.viewport.polygons:
            return
        
        if self.viewport.selected_polygon is None:
            self.viewport.select_polygon(0)
        else:
            next_idx = (self.viewport.selected_polygon + 1) % len(self.viewport.polygons)
            self.viewport.select_polygon(next_idx)
        
        self.status_label.setText(f"Selected polygon {self.viewport.selected_polygon + 1}/{len(self.viewport.polygons)}")
    
    def _on_select_previous(self):
        """Select previous polygon (Shift+Tab key)."""
        if not self.viewport.polygons:
            return
        
        if self.viewport.selected_polygon is None:
            self.viewport.select_polygon(len(self.viewport.polygons) - 1)
        else:
            prev_idx = (self.viewport.selected_polygon - 1) % len(self.viewport.polygons)
            self.viewport.select_polygon(prev_idx)
        
        self.status_label.setText(f"Selected polygon {self.viewport.selected_polygon + 1}/{len(self.viewport.polygons)}")
    
    def _on_quick_generate_sides(self, sides: int):
        """Quick generate polygon with specific number of sides (3-9 keys)."""
        try:
            if not self.current_generator:
                # Try to auto-select basic generator
                gen_class = self.generator_registry.get('basic')
                if gen_class:
                    enable_3d = self.generator_panel.is_3d_mode()
                    self.current_generator = gen_class(self.assembly, enable_3d_mode=enable_3d)
                else:
                    self.status_label.setText("No generator available")
                    return
            
            # Generate single polygon with specified sides
            poly_ids = self.current_generator.generate(method='single', sides=sides)
            
            if poly_ids:
                self._update_viewport_from_assembly()
                self.status_label.setText(f"Generated {sides}-sided polygon")
            
        except Exception as e:
            self.status_label.setText(f"Error: {e}")
            print(f"❌ Quick generate error: {e}")
    
    def _on_camera_rotate(self, dx: float, dy: float):
        """Rotate camera (Arrow keys)."""
        self.viewport.camera_angle_y += dx * 0.5
        self.viewport.camera_angle_x += dy * 0.5
        self.viewport.camera_angle_x = max(-89, min(89, self.viewport.camera_angle_x))
        self.viewport.update()
    
    def _on_camera_zoom(self, factor: float):
        """Zoom camera (+/- keys)."""
        self.viewport.camera_distance *= factor
        self.viewport.camera_distance = max(1.0, min(50.0, self.viewport.camera_distance))
        self.viewport.update()
    
    def _on_show_shortcuts_help(self):
        """Show keyboard shortcuts help dialog (F1 key)."""
        help_text = """
<h3>Keyboard Shortcuts</h3>

<h4>File Operations</h4>
<b>Ctrl+N</b> - New Assembly<br>
<b>Ctrl+O</b> - Load Assembly<br>
<b>Ctrl+S</b> - Save Assembly<br>
<b>Ctrl+Q</b> - Quit Application<br>

<h4>Edit Operations</h4>
<b>Ctrl+Z</b> - Undo<br>
<b>Ctrl+Y</b> - Redo<br>
<b>Delete</b> - Delete Selected Polygon<br>

<h4>View Operations</h4>
<b>Home</b> - Reset View<br>
<b>F</b> - Focus Viewport<br>
<b>3</b> - Toggle 3D Mode<br>
<b>Arrow Keys</b> - Rotate Camera<br>
<b>+/-</b> - Zoom In/Out<br>

<h4>Generation</h4>
<b>G</b> - Generate with Current Settings<br>
<b>P</b> - Place Polygon<br>
<b>E</b> - Explore Mode<br>
<b>3-9</b> - Quick Generate N-sided Polygon<br>

<h4>Bonding</h4>
<b>B</b> - Discover Bonds<br>

<h4>Selection</h4>
<b>Escape</b> - Deselect All<br>
<b>Tab</b> - Select Next<br>
<b>Shift+Tab</b> - Select Previous<br>

<h4>Help</h4>
<b>F1</b> - Show This Help
        """
        
        QMessageBox.information(self, "Keyboard Shortcuts", help_text)
    
    # === Validation Methods ===
    
    def _validate_bond_creation(self, bond_data: dict) -> dict:
        """Validate that creating a bond won't cause collisions or invalid geometry."""
        try:
            poly1 = self.assembly.get_polyform(bond_data['poly1_id'])
            poly2 = self.assembly.get_polyform(bond_data['poly2_id'])
            
            if not poly1 or not poly2:
                return {'valid': False, 'reason': 'One or both polyforms not found'}
            
            # Check if polyforms have 3D meshes for collision detection
            if not poly1.get('has_3d_mesh') or not poly2.get('has_3d_mesh'):
                # Can't validate without 3D mesh, allow it
                return {'valid': True, 'reason': 'No 3D mesh - validation skipped'}
            
            # Check for immediate collision
            if self.collision_validator.check_pair_collision(poly1, poly2):
                return {'valid': False, 'reason': 'Polyforms would collide when bonded'}
            
            # Check self-intersections
            if self.collision_validator.check_self_intersection(poly1):
                return {'valid': False, 'reason': f'Polyform {bond_data["poly1_id"]} has self-intersecting geometry'}
            
            if self.collision_validator.check_self_intersection(poly2):
                return {'valid': False, 'reason': f'Polyform {bond_data["poly2_id"]} has self-intersecting geometry'}
            
            return {'valid': True, 'reason': 'Validation passed'}
            
        except Exception as e:
            print(f"❌ Validation error: {e}")
            # If validation fails due to error, allow the operation
            return {'valid': True, 'reason': f'Validation error: {e}'}
    
    def _on_validate_assembly(self):
        """Validate entire assembly for collisions and issues (Ctrl+T)."""
        try:
            self.status_label.setText("Validating assembly...")
            
            # Run comprehensive validation
            reports = self.collision_validator.check_assembly_collisions(self.assembly)
            
            if not reports:
                self.status_label.setText("Validation passed - no issues found")
                QMessageBox.information(self, "Validation Passed", 
                                      "✓ Assembly validation passed!\n\nNo collisions or issues detected.")
                return
            
            # Format validation report
            error_count = sum(1 for r in reports if r['severity'] == 'error')
            warning_count = sum(1 for r in reports if r['severity'] == 'warning')
            
            report_text = f"Found {len(reports)} issue(s):\n"
            report_text += f"  Errors: {error_count}\n"
            report_text += f"  Warnings: {warning_count}\n\n"
            
            for i, report in enumerate(reports[:10]):  # Show first 10
                icon = "❌" if report['severity'] == 'error' else "⚠️"
                report_text += f"{icon} {report['message']}\n"
            
            if len(reports) > 10:
                report_text += f"\n... and {len(reports) - 10} more issue(s)"
            
            self.status_label.setText(f"Validation found {len(reports)} issue(s)")
            
            # Show warning dialog
            QMessageBox.warning(self, "Validation Issues Found", report_text)
            
        except Exception as e:
            self.status_label.setText(f"Validation error: {e}")
            print(f"❌ Validation error: {e}")
            import traceback
            traceback.print_exc()
    
    def _on_toggle_validation(self, checked: bool):
        """Toggle validation on/off."""
        self.validation_enabled = checked
        status = "enabled" if checked else "disabled"
        self.status_label.setText(f"Validation {status}")
        print(f"✓ Validation {status}")
    
    def _load_assembly_by_id(self, entry_id: str):
        """Load an assembly from library by ID."""
        try:
            self.status_label.setText("Loading assembly...")
            
            # Load entry from library
            entry = self.stable_library.load_entry(entry_id)
            
            if not entry:
                QMessageBox.warning(self, "Load Failed", "Could not load assembly from library.")
                return
            
            # Clear current assembly
            self.viewport.clear()
            self.assembly.polyforms.clear()
            self.assembly.bonds.clear()
            self.hinge_manager.clear()
            
            # Load polyforms and bonds
            self.stable_library.add_entry_to_assembly(self.assembly, entry_id)
            
            # Restore hinge data if available
            if 'hinge_data' in entry:
                try:
                    # Build ID map for hinge restoration
                    id_map = {}
                    for old_poly in entry.get('polyforms', []):
                        old_id = old_poly.get('id')
                        # Find corresponding new polyform in assembly
                        for new_poly in self.assembly.get_all_polyforms():
                            # Match by vertices or position
                            if self._polyforms_match(old_poly, new_poly):
                                id_map[old_id] = new_poly['id']
                                break
                    
                    # Deserialize and restore hinges
                    hinges = self.stable_library._deserialize_hinge_data(entry['hinge_data'], id_map)
                    
                    from hinge_manager import Hinge
                    for hinge_dict in hinges:
                        hinge = Hinge(
                            poly1_id=hinge_dict['poly1_id'],
                            poly2_id=hinge_dict['poly2_id'],
                            edge1_idx=hinge_dict['edge1_idx'],
                            edge2_idx=hinge_dict['edge2_idx'],
                            axis_start=hinge_dict['axis_start'],
                            axis_end=hinge_dict['axis_end'],
                            fold_angle=hinge_dict['fold_angle'],
                            is_active=hinge_dict['is_active']
                        )
                        self.hinge_manager.graph.add_hinge(hinge)
                    
                    print(f"✓ Restored {len(hinges)} hinges")
                    
                except Exception as e:
                    print(f"⚠️ Could not restore hinge data: {e}")
            
            # Update viewport
            self._update_viewport_from_assembly()
            
            # Update bonding panel
            self.bonding_panel.update_bonds_list(self.assembly.get_bonds())
            
            # Update counts
            polyform_count = len(self.assembly.get_all_polyforms())
            bond_count = len(self.assembly.get_bonds())
            
            self.polyforms_label.setText(f"Polyforms: {polyform_count}")
            self.status_label.setText(f"Loaded: {entry.get('name', 'Assembly')}")
            
            QMessageBox.information(self, "Assembly Loaded", 
                                  f"✓ Assembly loaded successfully!\n\nName: {entry.get('name', 'Unnamed')}\nPolyforms: {polyform_count}\nBonds: {bond_count}")
            
            print(f"✓ Assembly loaded: {entry.get('name')} ({polyform_count} polyforms, {bond_count} bonds)")
            
        except Exception as e:
            self.status_label.setText(f"Load error: {e}")
            print(f"❌ Load error: {e}")
            import traceback
            traceback.print_exc()
    
    def _polyforms_match(self, poly1: dict, poly2: dict) -> bool:
        """Check if two polyforms match (for ID mapping during load)."""
        # Simple heuristic: match by number of sides and position
        if poly1.get('sides') != poly2.get('sides'):
            return False
        
        pos1 = poly1.get('position', [0, 0, 0])
        pos2 = poly2.get('position', [0, 0, 0])
        
        # Check if positions are close
        import math
        dist = math.sqrt(sum((a - b) ** 2 for a, b in zip(pos1[:3], pos2[:3])))
        return dist < 0.01  # Small epsilon for floating point comparison
    
    # === Legacy Methods ===
    
    def _explore_step(self):
        """Execute one step of exploration."""
        # Legacy exploration - keeping for compatibility
        self.status_label.setText("Legacy exploration not yet connected")
