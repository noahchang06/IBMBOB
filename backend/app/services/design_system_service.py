from app.models.design_system import DesignSystem, TypeScale, ColorToken, Palette, SpacingScale, ComponentStyle
from app.models.graph import ReasoningGraph
from app.models.constraints import ConstraintSet, ConstraintKey
from app.models.common import DerivationLabel


class DesignSystemService:
    """Generates a complete design system from graph state and constraint values.
    
    All outputs are deterministic [SYSTEM] derivation — no LLM involvement.
    The constraint values directly modulate every design token.
    """

    def generate_design_system(self, graph: ReasoningGraph, constraints: ConstraintSet) -> DesignSystem:
        acc = self._get(constraints, ConstraintKey.accessibility, 0.5)
        density = self._get(constraints, ConstraintKey.information_density, 0.5)
        play = self._get(constraints, ConstraintKey.playfulness, 0.5)
        tension = self._get(constraints, ConstraintKey.visual_tension, 0.5)
        scarcity = self._get(constraints, ConstraintKey.material_scarcity, 0.5)

        typography = self._derive_typography(acc, density, play, tension, scarcity)
        palette = self._derive_palette(acc, density, play, tension, scarcity)
        spacing = self._derive_spacing(acc, density, scarcity)
        components = self._derive_components(acc, density, play, tension, scarcity)
        motion = self._derive_motion(play, tension, scarcity)

        wcag = "AAA" if acc > 0.8 else ("AA" if acc > 0.5 else "A")

        return DesignSystem(
            typography=typography,
            palette=palette,
            spacing=spacing,
            components=components,
            motion_duration_ms=motion[0],
            motion_easing=motion[1],
            wcag_level=wcag,
            derivation=DerivationLabel.SYSTEM,
        )

    def _get(self, constraints: ConstraintSet, key: ConstraintKey, default: float) -> float:
        if isinstance(constraints, dict):
            return constraints.get(key.value if isinstance(key, ConstraintKey) else key, default)
        return getattr(constraints, key.value if isinstance(key, ConstraintKey) else key, default)

    def _derive_typography(self, acc, density, play, tension, scarcity) -> TypeScale:
        # Base size: accessibility increases it, density decreases it
        base_size = 16
        base_size += round((acc - 0.5) * 6)    # +3 at max, -3 at min
        base_size -= round((density - 0.5) * 4) # -2 at max, +2 at min
        base_size = max(12, min(22, base_size))

        # Heading font: playful → rounded, scarce → mono, default → Inter
        if play > 0.65:
            heading_family = "Space Grotesk, sans-serif"
        elif scarcity > 0.7:
            heading_family = "JetBrains Mono, monospace"
        else:
            heading_family = "Inter, sans-serif"

        # Scale ratio: tension increases contrast, density compresses
        scale_ratio = 1.25
        scale_ratio += (tension - 0.5) * 0.3    # up to 1.40
        scale_ratio -= (density - 0.5) * 0.2    # down to 1.15
        scale_ratio = round(max(1.1, min(1.5, scale_ratio)), 3)

        # Weight: tension → bolder, scarcity → lighter
        heading_weight = "600" if tension > 0.5 else "500"
        if scarcity > 0.7:
            heading_weight = "400"

        # Line height: accessibility demands more
        line_height = 1.4 + (acc - 0.5) * 0.3
        line_height = round(max(1.3, min(1.8, line_height)), 2)

        return TypeScale(
            heading_family=heading_family,
            heading_weight=heading_weight,
            body_family="Inter, sans-serif",
            body_weight="400",
            base_size=base_size,
            scale_ratio=scale_ratio,
            line_height=line_height,
        )

    def _derive_palette(self, acc, density, play, tension, scarcity) -> Palette:
        """Generate palette from constraint values.
        
        The base palette is a professional clinical palette.
        Constraints modulate hue, saturation, and number of colors.
        """
        colors = []

        # Primary: clinical blue by default, shifts with playfulness
        if play > 0.65:
            primary_hex = "#6C5CE7"  # Playful purple
        elif tension > 0.65:
            primary_hex = "#E84393"  # High-tension pink
        elif scarcity > 0.65:
            primary_hex = "#2D3436"  # Minimal dark
        else:
            primary_hex = "#0984E3"  # Clinical blue

        colors.append(ColorToken(
            name="Primary", hex=primary_hex, role="primary",
            contrast_ratio=4.5 if acc < 0.7 else 7.0,
            derivation=DerivationLabel.SYSTEM,
        ))

        # Secondary
        if play > 0.65:
            secondary_hex = "#00CEC9"
        elif tension > 0.65:
            secondary_hex = "#FDCB6E"
        elif scarcity > 0.65:
            secondary_hex = "#636E72"
        else:
            secondary_hex = "#74B9FF"

        colors.append(ColorToken(
            name="Secondary", hex=secondary_hex, role="secondary",
            contrast_ratio=4.5,
            derivation=DerivationLabel.SYSTEM,
        ))

        # Accent: only if not scarce
        if scarcity < 0.65:
            if play > 0.65:
                accent_hex = "#FF6B6B"
            elif tension > 0.65:
                accent_hex = "#A29BFE"
            else:
                accent_hex = "#55EFC4"
            colors.append(ColorToken(
                name="Accent", hex=accent_hex, role="accent",
                derivation=DerivationLabel.SYSTEM,
            ))

        # Surface colors
        bg = "#FFFFFF" if scarcity > 0.6 else "#F8F9FA"
        fg = "#1A1A2E" if tension > 0.5 else "#2D3436"
        
        colors.append(ColorToken(
            name="Surface", hex=bg, role="surface",
            derivation=DerivationLabel.SYSTEM,
        ))
        colors.append(ColorToken(
            name="Text", hex=fg, role="text",
            contrast_ratio=15.0 if acc > 0.7 else 8.0,
            derivation=DerivationLabel.SYSTEM,
        ))

        # Status colors
        colors.append(ColorToken(
            name="Error", hex="#D63031", role="error",
            contrast_ratio=7.0 if acc > 0.7 else 4.5,
            derivation=DerivationLabel.SYSTEM,
        ))
        colors.append(ColorToken(
            name="Warning", hex="#FDCB6E", role="warning",
            derivation=DerivationLabel.SYSTEM,
        ))
        colors.append(ColorToken(
            name="Success", hex="#00B894", role="success",
            derivation=DerivationLabel.SYSTEM,
        ))

        return Palette(
            colors=colors,
            background=bg,
            foreground=fg,
            derivation=DerivationLabel.SYSTEM,
        )

    def _derive_spacing(self, acc, density, scarcity) -> SpacingScale:
        # Base unit: density reduces, accessibility increases
        base = 8
        if density > 0.65:
            base = 4
        elif acc > 0.65:
            base = 12
        elif scarcity > 0.65:
            base = 8

        # Scale multipliers
        scale = [1, 2, 3, 4, 6, 8, 12, 16]
        if density > 0.7:
            scale = [1, 2, 3, 4, 5, 6, 8, 10]  # Tighter progression
        elif acc > 0.7:
            scale = [2, 3, 4, 6, 8, 12, 16, 24]  # More generous

        return SpacingScale(base=base, scale=scale, unit="px")

    def _derive_components(self, acc, density, play, tension, scarcity) -> list[ComponentStyle]:
        # Border radius
        if play > 0.65:
            br = "16px"
        elif tension > 0.7 or scarcity > 0.7:
            br = "2px"
        elif acc > 0.7:
            br = "8px"
        else:
            br = "6px"

        # Padding
        if density > 0.65:
            btn_pad = "6px 12px"
            card_pad = "12px"
            input_pad = "6px 10px"
        elif acc > 0.65:
            btn_pad = "12px 24px"
            card_pad = "24px"
            input_pad = "12px 16px"
        else:
            btn_pad = "8px 16px"
            card_pad = "16px"
            input_pad = "8px 12px"

        # Shadow
        if scarcity > 0.6:
            shadow = "none"
        elif tension > 0.6:
            shadow = "0 4px 12px rgba(0,0,0,0.15)"
        else:
            shadow = "0 2px 4px rgba(0,0,0,0.08)"

        return [
            ComponentStyle(
                name="button", border_radius=br, padding=btn_pad, shadow=shadow,
                notes=f"Border radius driven by playfulness ({play:.1f}), shadow by scarcity ({scarcity:.1f})"
            ),
            ComponentStyle(
                name="card", border_radius=br, padding=card_pad, shadow=shadow,
                notes=f"Padding driven by density ({density:.1f}) and accessibility ({acc:.1f})"
            ),
            ComponentStyle(
                name="input", border_radius=br, padding=input_pad, shadow="none",
                notes=f"Input sizing optimized for density ({density:.1f})"
            ),
        ]

    def _derive_motion(self, play, tension, scarcity) -> tuple[int, str]:
        # Duration: playful → longer, scarce → shorter
        duration = 200
        duration += round((play - 0.5) * 200)    # up to 300ms
        duration -= round((scarcity - 0.5) * 100) # down to 150ms
        duration = max(100, min(400, duration))

        # Easing: playful → bouncy, tense → sharp
        if play > 0.65:
            easing = "cubic-bezier(0.34, 1.56, 0.64, 1)"  # Bounce
        elif tension > 0.65:
            easing = "cubic-bezier(0.16, 1, 0.3, 1)"  # Snap
        else:
            easing = "cubic-bezier(0.4, 0, 0.2, 1)"  # Standard ease

        return duration, easing
