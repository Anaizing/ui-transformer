using UnityEngine;
using UnityEngine.UIElements;
using System.Collections.Generic;
using System.Linq;

namespace YourUnityProject.UI.MaterialUI
{
    public class MuiButton : UnityEngine.UIElements.Button
    {
        // UXML Class Name for this component
        public new static readonly string ussClassName = "MuiButton-root";

        private VisualElement _loadingSpinner;
        private Label _innerTextLabel;

        public MuiButton()
        {
            AddToClassList(ussClassName);
            // Add any common initial setup here, e.g., default styles, children creation
            // Query and store references to child elements (expected in UXML)
            RegisterCallback<AttachToPanelEvent>(OnAttachToPanel);
            RegisterCallback<DetachFromPanelEvent>(OnDetachFromPanel);
        }

        private void OnAttachToPanel(AttachToPanelEvent evt)
        {
            _loadingSpinner = this.Q<VisualElement>("loading-spinner");
            _innerTextLabel = this.Q<Label>("inner-text-label");
            UpdateLoadingState(); // Initial update based on UXML value
        }

        private void OnDetachFromPanel(DetachToPanelEvent evt)
        {
            _loadingSpinner = null;
            _innerTextLabel = null;
        }

        private string _classes;
        public string Classes
        {
            get => _classes;
            set
            {
                if (_classes == value) return;
                _classes = value;
                // Add logic to update UI based on this prop if necessary
            }
        }

        private string _color;
        public string Color
        {
            get => _color;
            set
            {
                if (_color == value) return;
                _color = value;
                // Add logic to update UI based on this prop if necessary
            }
        }

        private bool _disabled;
        public bool Disabled
        {
            get => _disabled;
            set
            {
                if (_disabled == value) return;
                _disabled = value;
                SetEnabled(!value);
                EnableInClassList("Mui-disabled", value);
            }
        }

        private bool _disableelevation;
        public bool DisableElevation
        {
            get => _disableelevation;
            set
            {
                if (_disableelevation == value) return;
                _disableelevation = value;
                // Add logic to update UI based on this prop if necessary
            }
        }

        private bool _disablefocusripple;
        public bool DisableFocusRipple
        {
            get => _disablefocusripple;
            set
            {
                if (_disablefocusripple == value) return;
                _disablefocusripple = value;
                // Add logic to update UI based on this prop if necessary
            }
        }

        private bool _disableripple;
        public bool DisableRipple
        {
            get => _disableripple;
            set
            {
                if (_disableripple == value) return;
                _disableripple = value;
                // Add logic to update UI based on this prop if necessary
            }
        }

        private string _endicon;
        public string EndIcon
        {
            get => _endicon;
            set
            {
                if (_endicon == value) return;
                _endicon = value;
                // Add logic to update UI based on this prop if necessary
            }
        }

        private bool _fullwidth;
        public bool FullWidth
        {
            get => _fullwidth;
            set
            {
                if (_fullwidth == value) return;
                _fullwidth = value;
                // Add logic to update UI based on this prop if necessary
            }
        }

        private string _href;
        public string Href
        {
            get => _href;
            set
            {
                if (_href == value) return;
                _href = value;
                // Add logic to update UI based on this prop if necessary
            }
        }

        private bool _loading;
        public bool Loading
        {
            get => _loading;
            set
            {
                if (_loading == value) return;
                _loading = value;
                UpdateLoadingState();
            }
        }

        private string _loadingindicator;
        public string LoadingIndicator
        {
            get => _loadingindicator;
            set
            {
                if (_loadingindicator == value) return;
                _loadingindicator = value;
                // Add logic to update UI based on this prop if necessary
            }
        }

        private string _loadingPosition = "";
        public string LoadingPosition
        {
            get => _loadingPosition;
            set
            {
                if (_loadingPosition == value) return;
                _loadingPosition = value;
                UpdateLoadingState();
            }
        }

        private string _size;
        public string Size
        {
            get => _size;
            set
            {
                if (_size == value) return;
                _size = value;
                // Add logic to update UI based on this prop if necessary
            }
        }

        private string _starticon;
        public string StartIcon
        {
            get => _starticon;
            set
            {
                if (_starticon == value) return;
                _starticon = value;
                // Add logic to update UI based on this prop if necessary
            }
        }

        private string _variant;
        public string Variant
        {
            get => _variant;
            set
            {
                if (_variant == value) return;
                _variant = value;
                // Add logic to update UI based on this prop if necessary
            }
        }

        private void UpdateLoadingState()
        {
            if (_loadingSpinner == null || _innerTextLabel == null) return;

            if (Loading)
            {
                _loadingSpinner.style.display = DisplayStyle.Flex;
                _innerTextLabel.style.display = DisplayStyle.None;
                // Adjust flex direction and justification based on LoadingPosition
                if (LoadingPosition == "start")
                {
                    style.flexDirection = FlexDirection.Row;
                    style.justifyContent = JustifyContent.FlexStart;
                }
                else if (LoadingPosition == "end")
                {
                    style.flexDirection = FlexDirection.RowReverse;
                    style.justifyContent = JustifyContent.FlexEnd;
                }
                else if (LoadingPosition == "center" || LoadingPosition == "")
                {
                    style.flexDirection = FlexDirection.Row;
                    style.justifyContent = JustifyContent.Center;
                }
            }
            else
            {
                _loadingSpinner.style.display = DisplayStyle.None;
                _innerTextLabel.style.display = DisplayStyle.Flex;
                // Reset to default layout if not loading
                style.flexDirection = FlexDirection.Row;
                style.justifyContent = JustifyContent.Center;
            }
        }

        public new class UxmlFactory : UxmlFactory<MuiButton, UxmlTraits> {}

        public new class UxmlTraits : UnityEngine.UIElements.Button.UxmlTraits
        {
            private UxmlStringAttribute _classesAttribute = new UxmlStringAttribute { name = "classes" };
            private UxmlStringAttribute _colorAttribute = new UxmlStringAttribute { name = "color" };
            private UxmlBoolAttribute _disabledAttribute = new UxmlBoolAttribute { name = "disabled" };
            private UxmlBoolAttribute _disable_elevationAttribute = new UxmlBoolAttribute { name = "disable-elevation" };
            private UxmlBoolAttribute _disable_focus_rippleAttribute = new UxmlBoolAttribute { name = "disable-focus-ripple" };
            private UxmlBoolAttribute _disable_rippleAttribute = new UxmlBoolAttribute { name = "disable-ripple" };
            private UxmlStringAttribute _end_iconAttribute = new UxmlStringAttribute { name = "end-icon" };
            private UxmlBoolAttribute _full_widthAttribute = new UxmlBoolAttribute { name = "full-width" };
            private UxmlStringAttribute _hrefAttribute = new UxmlStringAttribute { name = "href" };
            private UxmlBoolAttribute _loadingAttribute = new UxmlBoolAttribute { name = "loading" };
            private UxmlStringAttribute _loading_indicatorAttribute = new UxmlStringAttribute { name = "loading-indicator" };
            private UxmlStringAttribute _loading_positionAttribute = new UxmlStringAttribute { name = "loading-position" };
            private UxmlStringAttribute _sizeAttribute = new UxmlStringAttribute { name = "size" };
            private UxmlStringAttribute _start_iconAttribute = new UxmlStringAttribute { name = "start-icon" };
            private UxmlStringAttribute _variantAttribute = new UxmlStringAttribute { name = "variant" };

            public override void Init(VisualElement ve, IUxmlAttributes bag, CreationContext cc)
            {
                base.Init(ve, bag, cc);
                var component = ve as MuiButton;
                if (component == null) return;

                component.Classes = _classesAttribute.GetValueFromBag(bag);
                component.Color = _colorAttribute.GetValueFromBag(bag);
                component.Disabled = _disabledAttribute.GetValueFromBag(bag);
                component.DisableElevation = _disable_elevationAttribute.GetValueFromBag(bag);
                component.DisableFocusRipple = _disable_focus_rippleAttribute.GetValueFromBag(bag);
                component.DisableRipple = _disable_rippleAttribute.GetValueFromBag(bag);
                component.EndIcon = _end_iconAttribute.GetValueFromBag(bag);
                component.FullWidth = _full_widthAttribute.GetValueFromBag(bag);
                component.Href = _hrefAttribute.GetValueFromBag(bag);
                component.Loading = _loadingAttribute.GetValueFromBag(bag);
                component.LoadingIndicator = _loading_indicatorAttribute.GetValueFromBag(bag);
                component.LoadingPosition = _loading_positionAttribute.GetValueFromBag(bag);
                component.Size = _sizeAttribute.GetValueFromBag(bag);
                component.StartIcon = _start_iconAttribute.GetValueFromBag(bag);
                component.Variant = _variantAttribute.GetValueFromBag(bag);
            }
        }
    }
}