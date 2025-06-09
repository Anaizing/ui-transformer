using UnityEngine;
using UnityEngine.UIElements;
using System.Collections.Generic;
using System.Linq;

namespace YourUnityProject.UI.MaterialUI
{
    public class MuiCard : UnityEngine.UIElements.VisualElement
    {
        // UXML Class Name for this component
        public new static readonly string ussClassName = "MuiCard-root";

        public MuiCard()
        {
            AddToClassList(ussClassName);
            // Add any common initial setup here, e.g., default styles, children creation
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

        private bool _raised;
        public bool Raised
        {
            get => _raised;
            set
            {
                if (_raised == value) return;
                _raised = value;
                // Add logic to update UI based on this prop if necessary
            }
        }

        public new class UxmlFactory : UxmlFactory<MuiCard, UxmlTraits> {}

        public new class UxmlTraits : UnityEngine.UIElements.VisualElement.UxmlTraits
        {
            private UxmlStringAttribute _classesAttribute = new UxmlStringAttribute { name = "classes" };
            private UxmlBoolAttribute _raisedAttribute = new UxmlBoolAttribute { name = "raised" };

            public override void Init(VisualElement ve, IUxmlAttributes bag, CreationContext cc)
            {
                base.Init(ve, bag, cc);
                var component = ve as MuiCard;
                if (component == null) return;

                component.Classes = _classesAttribute.GetValueFromBag(bag);
                component.Raised = _raisedAttribute.GetValueFromBag(bag);
            }
        }
    }
}