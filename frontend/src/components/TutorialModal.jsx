
import "../styles/Modal.css"
import "../styles/TutorialModal.css"

function TutorialModal({ isOpen, onClose }) {
    if (!isOpen) return null

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="tut-modal" onClick={(e) => e.stopPropagation()}>
                <div className="modal-header">
                    <h2>How to use</h2>
                    <button className="modal-close" onClick={onClose}>×</button>
                </div>

                <div className="modal-content">
                    <p>Currently, there are only 2 features that can be used</p>
                    <ol>
                        <li><b>Image editing</b>:<br/> if you provide an image and specify the type of mood you would like to be conveyed in the image, you will get an output image (hopefully it can inspire you!)</li>
                        <li><b>Colour scheme</b>: <br/>if you ask for a colour scheme for a potential piece by specifying a kind of mood to convey, you will get a colour scheme (consists of 5 colours). <br/>You can also provide an optional image that may be used to inspire some of the output colours!</li>
                    </ol>
                    The language model is not very complex, so please be patient and try rephrasing things if it doesn't understand your prompt.
                </div>
            </div>
        </div>
    )
}

export default TutorialModal